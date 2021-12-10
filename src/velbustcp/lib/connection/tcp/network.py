import threading
import socket
import ssl
import logging
import sys
from typing import List, Optional

if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol

from velbustcp.lib.packet.packetexcluder import should_accept
from velbustcp.lib.connection.tcp.client import Client
from velbustcp.lib.connection.tcp.clientconnection import ClientConnection
from velbustcp.lib.settings.network import NetworkSettings


class OnNetworkPacketReceived(Protocol):
    def __call__(self, client: Client, packet: bytearray) -> None:
        pass


class Network():

    on_packet_received: OnNetworkPacketReceived

    __clients: List[Client]

    def __init__(self, options: NetworkSettings):
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

        return self.__options.relay

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
                client_socket, address = self.__bind_socket.accept()

                # Make sure that we're still active
                if self.is_active():

                    self.__logger.info("TCP connection from %s", address)

                    if self.__options.ssl:

                        try:
                            client_socket = self.__context.wrap_socket(client_socket, server_side=True)

                        except ssl.SSLError as e:
                            self.__logger.exception("Couldn't wrap socket")
                            raise e

                    # Define client connection
                    connection = ClientConnection()
                    connection.socket = client_socket
                    connection.should_authorize = self.__options.auth
                    connection.authorization_key = self.__options.auth_key

                    # Start client
                    client = Client(connection)
                    client.on_packet_receive = self.__on_packet_received
                    client.on_close = self.__on_client_close
                    client.start()

                    with self.__clients_lock:
                        self.__clients.append(client)

            except Exception:
                self.__logger.exception("Couldn't accept socket")

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
        if not client.is_authorized():
            self.__logger.info("TCP connection closed %s [auth failed]", client.address())
        else:
            self.__logger.info("TCP connection closed %s", client.address())

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
        self.__bind_socket.bind(self.__options.address)
        self.__bind_socket.listen(0)

        if self.__options.ssl:
            self.__context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            self.__context.load_cert_chain(self.__options.cert, keyfile=self.__options.pk)

        self.__logger.info("Listening to TCP connections on %s [SSL:%s]", self.__options.address, "enabled" if self.__options.ssl else "disabled")

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

            self.__logger.info("Stopping TCP connection %s", self.__options.address)

            # Set running to false
            self.__running = False

            # Stop every client listening
            with self.__clients_lock:
                for client in self.__clients:
                    client.stop()

            # Connect to itself to stop the blocking accept
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("127.0.0.1", self.__options.port))

            # Wait till the server thread is closed
            self.__server_thread.join()

            # Close the socket
            self.__bind_socket.close()

            self.__logger.info("Stopped TCP connection %s", self.__options.address)
