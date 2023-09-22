import threading
import socket
import ssl
import logging
import platform
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
        # Indicate that the server should be terminated (but does not necessarily indicate that it
        # is has been terminated.
        self.__stop: threading.Event = threading.Event()
        self.__stop.set()
        self.__bind_socket: Optional[socket.socket] = None
        self.__context: Optional[ssl.SSLContext] = None
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

    def __get_bound_socket(self) -> socket.socket:
        RETRY_DELAY = 5.0

        while self.is_active() and not self.__bind_socket:
            # First, try to initialize the SSL context (as we only need to do it once and once done
            # we won’t need to return to trying this, most likely.)
            if self.__options.ssl and not self.__context:
                try:
                    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                    context.load_cert_chain(self.__options.cert, keyfile=self.__options.pk)
                    self.__context = context
                except Exception as e:
                    self.__logger.error("Could not initialize SSL for %s: %s", self.__options.address, e)
                    self.__stop.wait(RETRY_DELAY)
                    continue

            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

            # On Linux the following socket option succeeds binding to the specified IP address
            # even if it is not currently assigned to any of the interfaces, which foregoes the
            # need for this entire retry logic (still necessary for non-Linux systems) that
            # follows.
            #
            # FreeBSD has IP_BINDANY and OpenBSD has SO_BINDANY, but at least the latter is a
            # privileged operation.
            if platform.system() == "Linux":
                try:
                    IP_FREEBIND = 15
                    sock.setsockopt(socket.SOL_IP, IP_FREEBIND, 1)
                except Exception as e:
                    self.__logger.debug("Could not set IP_FREEBIND for socket at %s: %s", self.__options.address, e)

            try:
                sock.bind(self.__options.address)
            except OSError as e:
                self.__logger.error("Could not bind to %s: %s", self.__options.address, e)
                self.__stop.wait(RETRY_DELAY)
                continue

            try:
                sock.listen(0)
            except OSError as e:
                self.__logger.error("Could not listen on %s: %s", self.__options.address, e)
                self.__stop.wait(RETRY_DELAY)
                continue

            self.__bind_socket = sock
            self.__logger.info("Listening to TCP connections on %s [SSL:%s]", self.__options.address, "enabled" if self.__options.ssl else "disabled")
        return self.__bind_socket


    def __bind_and_accept_sockets(self) -> None:
        """Binds a listener socket and accept clients from it.

        If the tcp server is closed it will also close socket
        """

        while self.is_active():
            try:
                client_socket, address = self.__get_bound_socket().accept()
            except OSError as e:
                self.__logger.error("Couldn't accept socket: %s", e)
                continue

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


    def is_active(self) -> bool:
        """Returns whether or not the TCP connection is active

        Returns:
            bool: Whether or not the TCP connection is active
        """

        return not self.__stop.is_set()

    def start(self) -> None:
        """Starts up the TCP server
        """

        if self.is_active():
            return
        self.__stop.clear()

        # Start the server thread to handle connections
        self.__server_thread = threading.Thread(target=self.__bind_and_accept_sockets)
        self.__server_thread.name = "TCP server thread " + self.__options.host + ":" + str(self.__options.port)
        self.__server_thread.start()

    def stop(self) -> None:
        """Stops the TCP server
        """

        if not self.is_active():
            return

        self.__logger.info("Stopping TCP connection %s", self.__options.address)
        self.__stop.set()

        # Stop accepting further connections.
        try:
            # Shutting down the socket also interrupts the `accept` call within the
            # __server_thread, thus terminating it.
            self.__bind_socket.shutdown(socket.SHUT_RDWR)
            self.__bind_socket.close()
            self.__bind_socket = None
        except AttributeError:
            pass

        # Wait till the server thread is closed
        self.__server_thread.join()

        # Stop every client listening
        with self.__clients_lock:
            for client in self.__clients:
                client.stop()

        self.__logger.info("Stopped TCP connection %s", self.__options.address)
