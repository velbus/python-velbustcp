import logging
import threading
import socket
from typing import Any, Optional, List

from velbustcp.lib.connection.tcp.clientconnection import ClientConnection
from velbustcp.lib.packet.packetparser import PacketParser
from velbustcp.lib.signals import on_tcp_receive, on_client_close


class Client():

    def __init__(self, connection: ClientConnection):
        """Initialises a network client.

        Args:
            connection (ClientConnection): The ClientConnection for the client.
        """

        self.__logger: logging.Logger = logging.getLogger("__main__." + __name__)
        self.__connection: ClientConnection = connection
        self.__is_active: bool = False
        self.__address: str = connection.socket.getpeername()
        self.__received_packets: List[bytearray] = []

    def start(self) -> None:
        """Starts receiving data from the client.
        """

        # Start a thread to handle receive
        if self.is_active():
            return

        self.__is_active = True
        self.__logger.info("Starting client connection for %s", self.address())
        self.__receive_thread = threading.Thread(target=self.__handle_client)
        self.__receive_thread.name = f"TCP-RECV: {self.address()}"
        self.__receive_thread.start()

    def stop(self) -> None:
        """Stops receiving data and disconnects from the client.
        """

        if not self.is_active():
            return

        self.__is_active = False
        self.__logger.info("Closing client connection for %s", self.address())
        self.__connection.socket.shutdown(socket.SHUT_RDWR)
        self.__connection.socket.close()
        self.__received_packets.clear()
        on_client_close.send(self)

    def send(self, data: bytearray):
        """Sends data to the client.

        Args:
            data (bytearray): The data to be sent.
        """

        if not self.is_active():
            return

        if data in self.__received_packets:
            self.__received_packets.remove(data)
            return

        self.__connection.socket.sendall(data)

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

    def __handle_client(self) -> None:
        """Bootstraps the client for communcation.
        """

        # Handle authorization, if not authorized stop client and return
        if not self.__handle_authorization():
            self.__logger.warning("Client authorization failed for %s", self.address())
            self.stop()
            return

        # Handle packets
        self.__handle_packets()

        # Make sure client communication is stopped
        self.stop()

    def __handle_authorization(self) -> bool:
        """Handles client authorization.

        Returns:
            bool: Whether or not the client is successfully authenticated.
        """

        if not self.__connection.should_authorize:
            return True

        try:
            data = self.__connection.socket.recv(1024)

            if not data:
                self.__logger.warning("Client %s disconnected before receiving authorization key", self.address())
                return False

            return self.__connection.authorization_key == data.decode("utf-8").strip()

        except Exception:
            self.__logger.exception("Exception during authorization for %s", self.address())

        return False

    def __handle_packets(self) -> None:
        """Receives packet until client is no longer active.
        """

        parser = PacketParser()

        # Receive data
        while self.is_active():

            data: Optional[bytes] = None

            try:
                data = self.__connection.socket.recv(1024)
            except Exception:
                self.__logger.exception("Exception during packet receiving")
                return

            # If no data received from the socket, the client disconnected
            # Break out of the loop
            if not data:
                self.__logger.info("Received no data from client %s", self.address())
                return

            packets = parser.feed(bytearray(data))

            for packet in packets:
                self.__received_packets.append(packet)
                on_tcp_receive.send(self, packet=packet)
