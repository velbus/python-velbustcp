import threading
import socket
import ssl
import logging
from typing import Any, Dict, List, Optional, Protocol, Tuple

from velbustcp.lib.packet.packetexcluder import should_accept
from velbustcp.lib.connection.client import Client


class OnNetworkPacketReceived(Protocol):
    def __call__(self, client: Client, packet: bytearray) -> None:
        pass


class Network():

    on_packet_received: OnNetworkPacketReceived

    __clients: List[Client]

    def __init__(self, options: Dict[str, Any]):
        """Initialises a TCP network.

        Args:
            options (dict): The options used to configure the network.
        """

        self.__logger = logging.getLogger(__name__)

        self.__clients = []
        self.__clients_lock = threading.Lock()
        self.__running = False
        self.__options = options

    def relay(self) -> bool:
        """Returns whether or not packets are relayed on this network.

        Returns:
            bool: Whether or not packets are relayed on this network.
        """

        return bool(self.__options["relay"])

    def host(self) -> str:
        """Returns the host that this network is bound to.

        Returns:
            str: The host of the network.
        """

        return str(self.__options["host"])

    def port(self) -> int:
        """Returns the port that this network is bound to.

        Returns:
            int: The port of the network.
        """

        return int(self.__options["port"])

    def address(self) -> Tuple[str, int]:
        """Returns the address that this network is bound to.

        Returns:
            Tuple[str, int]: A tuple containing the host and port of the network.
        """

        return (self.host(), self.port())

    def has_ssl(self) -> bool:
        """Returns whether or not TLS/SSL is enabled for this Network.

        Returns:
            bool: Whether or not TLS/SSL is enabled.
        """

        return bool(self.__options["ssl"])

    def has_auth(self) -> bool:
        """Returns whether or not authentication is enabled for this Network.

        Returns:
            bool: Whether or not authentication is enabled.
        """

        return bool(self.__options["auth"])

    def __auth_key(self) -> str:
        """Returns the authentication key.

        Returns:
            str: A string containing the authentication key.
        """

        return str(self.__options["authkey"])

    def send(self, data: bytearray, excluded_client: Optional[Client] = None) -> None:
        """Sends given data to all connected clients to the network. If excluded_client is supplied, will skip given excluded_client.

        Args:
            data (bytearray): Specifies what data to send to the connected clients
            excluded_client (Client, optional): Specifies which client to skip sending the data to. Defaults to None.
        """

        if excluded_client:
            assert isinstance(excluded_client, Client)

        self.__logger.debug("[TCP OUT] " + " ".join(hex(x) for x in data))

        if self.is_active():
            with self.__clients_lock:
                for client in self.__clients:

                    if client.is_active():

                        try:
                            if (client != excluded_client) and should_accept(data, client):
                                client.send(data)
                        except Exception:
                            continue

    def __accept_sockets(self) -> None:
        """Accepts clients from socket, if the tcp server is closed it will also close socket
        """

        while self.is_active():

            try:
                connection, address = self.__bind_socket.accept()

                # Make sure that we're still active
                if self.is_active():

                    self.__logger.info("TCP connection from {0}".format(str(address)))

                    if self.has_ssl():

                        try:
                            connection = self.__context.wrap_socket(connection, server_side=True)

                        except ssl.SSLError as e:
                            self.__logger.error("Couldn't wrap socket")
                            raise e

                    client = Client(connection)
                    client.on_packet_receive = self.__on_packet_received
                    client.on_close = self.__on_client_close

                    if self.has_auth():
                        client.set_should_authorize(self.__auth_key())

                    client.start()

                    with self.__clients_lock:
                        self.__clients.append(client)

            except Exception as e:
                self.__logger.error("Couldn't accept socket")
                self.__logger.exception(str(e))

        self.__bind_socket.close()
        self.__logger.info("Closed TCP socket")

    def __on_packet_received(self, client: Client, packet: bytearray):
        """Called on Client packet receive.

        Args:
            client (Client): The client which received the packet.
            packet (bytearray): The packet that is received.
        """

        # Make sure we should accept the packet
        if should_accept(packet, client):

            if self.on_packet_received:
                self.on_packet_received(client, packet)

    def __on_client_close(self, client: Client):
        """Called on Client tcp connection close.

        Args:
            client (Client): The client for which the connection closed.
        """

        # Warning message
        if self.__options["auth"] and not client.is_authorized():
            self.__logger.info("TCP connection closed {0} [auth failed]".format(str(client.address())))
        else:
            self.__logger.info("TCP connection closed {0}".format(str(client.address())))

    def is_active(self) -> bool:
        """Returns whether or not the TCP connection is active

        Returns:
            bool: Whether or not the TCP connection is active
        """

        return self.__running

    def start(self) -> None:
        """Starts up the TCP server
        """

        if self.is_active():
            return

        self.__bind_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__bind_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__bind_socket.bind(self.address())
        self.__bind_socket.listen(0)

        if self.has_ssl():
            self.__context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            self.__context.load_cert_chain(self.__options["cert"], keyfile=self.__options["pk"])

        self.__logger.info("Listening to TCP connections on {0}:{1} [SSL:{2}]".format(self.host(), self.port(), self.has_ssl()))

        # Now that we reached here, set running
        self.__running = True

        # Start the server thread to handle connections
        self.__server_thread = threading.Thread(target=self.__accept_sockets)
        self.__server_thread.name = 'TCP server thread'
        self.__server_thread.start()

    def stop(self) -> None:
        """Stops the TCP server
        """

        if self.is_active():

            self.__logger.info("Stopping TCP connection {0}:{1}".format(self.host(), self.port()))

            # Set running to false
            self.__running = False

            # Stop every client listening
            with self.__clients_lock:
                for client in self.__clients:
                    client.stop()

            # Connect to itself to stop the blocking accept
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("127.0.0.1", self.port()))

            # Wait till the server thread is closed
            self.__server_thread.join()
