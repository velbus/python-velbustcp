import threading
import socket
import ssl
import logging
from typing import List
from velbustcp.lib.connection.tcp.client import Client
from velbustcp.lib.connection.tcp.clientconnection import ClientConnection
from velbustcp.lib.settings.network import NetworkSettings
from velbustcp.lib.signals import on_client_close


class Network():

    def __init__(self, options: NetworkSettings):
        """Initialises a TCP network.

        Args:
            options (dict): The options used to configure the network.
        """

        # Hook up signal
        def handle_client_close(sender: Client, **kwargs):
            self.__logger.info("TCP connection closed %s", sender.address())

            if sender not in self.__clients:
                return

            with self.__clients_lock:
                self.__clients.remove(sender)
        self.handle_client_close = handle_client_close
        on_client_close.connect(handle_client_close)

        self.__logger: logging.Logger = logging.getLogger("__main__." + __name__)
        self.__clients: List[Client] = []
        self.__clients_lock: threading.Lock = threading.Lock()
        self.__running: bool = False
        self.__options: NetworkSettings = options

    def send(self, data: bytearray) -> None:
        """Sends given data to all connected clients to the network.

        Args:
            data (bytearray): Specifies the packet to send to the connected clients of this network.
        """

        if not self.is_active():
            return

        if not self.__options.relay:
            return

        if self.__logger.isEnabledFor(logging.DEBUG):  # pragma: no cover
            self.__logger.debug("[TCP OUT] %s", " ".join(hex(x) for x in data))

        with self.__clients_lock:
            for client in self.__clients:
                try:
                    client.send(data)
                except Exception:
                    self.__logger.exception("Could not send data to client %s", client.address())

    def __accept_sockets(self) -> None:
        """Accepts clients from socket, if the tcp server is closed it will also close socket
        """

        while self.is_active():

            try:
                client_socket, address = self.__bind_socket.accept()

                # Make sure that we're still active
                if not self.is_active():
                    return

                self.__logger.info("TCP connection from %s", address)

                if self.__options.ssl:
                    client_socket = self.__context.wrap_socket(client_socket, server_side=True)

                # Define client connection
                connection = ClientConnection()
                connection.socket = client_socket
                connection.should_authorize = self.__options.auth
                connection.authorization_key = self.__options.auth_key

                # Start client
                client = Client(connection)
                client.start()

                with self.__clients_lock:
                    self.__clients.append(client)

            except Exception:
                self.__logger.exception("Couldn't accept socket")

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
        self.__server_thread.name = "TCP server thread " + self.__options.host + ":" + str(self.__options.port)
        self.__server_thread.start()

    def stop(self) -> None:
        """Stops the TCP server
        """

        if not self.is_active():
            return

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
