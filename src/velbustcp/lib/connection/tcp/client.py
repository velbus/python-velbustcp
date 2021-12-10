import logging
import threading
import socket
import sys
from typing import Any

from velbustcp.lib.connection.tcp.clientconnection import ClientConnection

if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol

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
    __address: Any = ""

    def __init__(self, connection: ClientConnection):
        """Initialises a network client.

        Args:
            connection (ClientConnection): The ClientConnection for the client.
        """

        self.__logger = logging.getLogger(__name__)
        self.__connection = connection
        self.__authorized = False
        self.__is_active = False
        self.__address = connection.socket.getpeername()

    def start(self) -> None:
        """Starts receiving data from the client.
        """

        # Start a thread to handle receive
        if not self.is_active():
            self._receive_thread = threading.Thread(target=self.__bootstrap_client)
            self._receive_thread.name = f"TCP-RECV: {self.address()}"
            self._receive_thread.start()

    def stop(self) -> None:
        """Stops receiving data and disconnects from the client.
        """

        if self.is_active():
            self.__logger.info(f"Closing connection for {self.address()}")
            self.__is_active = False
            self.__connection.socket.shutdown(socket.SHUT_RDWR)
            self.__connection.socket.close()

            if self.on_close:
                self.on_close(self)

    def send(self, data: bytearray):
        """Sends data to the client.

        Args:
            data (bytearray): The data to be sent.
        """

        if self.is_active():
            self.__connection.socket.sendall(data)

    def is_authorized(self) -> bool:
        """Returns whether or not the client is authorized to send messages to the server.

        Returns:
            bool: Whether or not the client is authorized to send messages to the server.
        """

        return self.__authorized

    def is_active(self) -> bool:
        """Returns whether the client is active for communication.
        If applicable, this also means that the client is authenticated.

        Returns:
            bool: Whether the client is active for communication.
        """

        return self.is_authorized() and self.__is_active

    def address(self) -> Any:
        """Returns the address of the client.

        Returns:
            Any: The address of the client.
        """

        return self.__address

    def __bootstrap_client(self) -> None:
        """Bootstraps the client for communcation.
        """

        # Set the client active
        self.__is_active = True

        # Handle authorization
        self.__handle_authorization()

        # If authorized, start handling packets
        if self.is_authorized():
            self.__handle_packets()

        # Make sure client communication is stopped
        self.stop()

    def __handle_authorization(self) -> None:
        """Handles client authorization.
        """

        if not self.__connection.should_authorize:
            self.__authorized = True
            return

        try:
            data = self.__connection.socket.recv(1024)

            if not data:
                raise Exception("Client disconnected before receiving authorization key")

            self.__authorized = self.__connection.authorization_key == data.decode("utf-8").strip()

        except Exception:
            self.__logger.warn(f"Authorization failed for {self.address()}")

    def __handle_packets(self) -> None:
        """Receives packet until client is no longer active.
        """

        parser = PacketParser()

        # Receive data
        while self.is_active():

            try:
                data = self.__connection.socket.recv(1024)

                # If no data received from the socket, the client disconnected
                # Break out of the loop
                if not data:
                    break

                parser.feed(bytearray(data))
                packet = parser.next()
                while packet is not None:

                    if self.on_packet_receive:
                        self.on_packet_receive(self, packet)

                    packet = parser.next()

            # If an exception is thrown, log it
            except Exception:
                self.__logger.exception("Exception during packet receiving")
