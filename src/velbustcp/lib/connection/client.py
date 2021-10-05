import logging
import threading
import socket
from typing import Any, Protocol

from velbustcp.lib.packet.packetparser import PacketParser


class OnClientPacketReceived(Protocol):
    def __call__(self, client: Any, packet: bytearray) -> None:
        pass


class OnClientClose(Protocol):
    def __call__(self, client: Any) -> None:
        pass


class Client():

    on_packet_receive: OnClientPacketReceived
    on_close: OnClientClose

    def __init__(self, connection: socket.socket):
        """Initialises a network client.

        Args:
            connection (socket.socket): The socket for connection with the client.
        """

        self.__logger = logging.getLogger(__name__)

        self.__connection = connection
        self.__address = connection.getpeername()

        # Authorization details
        self.__should_authorize = False
        self.__authorized = False
        self.__authorize_key = ""

        self.__is_active = False

    def start(self) -> None:
        """Starts receiving data from the client.
        """

        # Start a thread to handle receive
        self._receive_thread = threading.Thread(target=self.__recv)
        self._receive_thread.name = 'Receive from client thread'
        self._receive_thread.start()

    def stop(self) -> None:
        """Stops receiving data and disconnects from the client.
        """

        if self.is_active():
            self.__is_active = False
            self.__connection.shutdown(socket.SHUT_RDWR)
            self.__connection.close()

            if self.on_close:
                self.on_close(self)

    def send(self, data: bytearray):
        """Sends data to the client.

        Args:
            data (bytearray): The data to be sent.
        """

        self.__connection.sendall(data)

    def set_should_authorize(self, authorize_key: str) -> None:
        """Flags the client so that the client must authorize first before sending messages to the server.

        Args:
            authorize_key (str): The authorization key that must be compared.
        """

        self.__authorize_key = authorize_key
        self.__should_authorize = True

    def is_authorized(self) -> bool:
        """Returns whether or not the client is authorized to send messages to the server.

        Returns:
            bool: Whether or not the client is authorized to send messages to the server.
        """

        if not self.__should_authorize:
            return True

        return self.__authorized

    def is_active(self) -> bool:
        """Returns whether the client is active for communication.
        If applicable, this also means that the client is authenticated.

        Returns:
            bool: Whether the client is active for communication.
        """

        return self.__is_active

    def address(self) -> Any:
        """Returns the address of the client.

        Returns:
            Any: The address of the client.
        """

        return self.__address

    def __recv(self) -> None:
        """Handles communication with the client.
        """

        self.__is_active = True

        # Handle authorization
        if self.__should_authorize:

            try:
                auth_key = self.__connection.recv(1024).decode("utf-8").strip()
            except Exception:
                self.stop()

            if self.__authorize_key == auth_key:
                self.__authorized = True

        parser = PacketParser()

        # Receive data
        while self.is_active() and self.is_authorized():

            try:
                data = self.__connection.recv(1024)

                # If program gets here without data, the client disconnected
                if not data:
                    break

                parser.feed(bytearray(data))
                packet = parser.next()
                while packet is not None:

                    if self.on_packet_receive:
                        self.on_packet_receive(self, packet)

                    packet = parser.next()

            except Exception as e:
                self.__logger.exception(str(e))
                break

        self.stop()
