import threading
import socket
import ssl
import logging
import sys
import os

from .. import packetexcluder
from .client import Client

class Network():

    def __init__(self, options, bridge):
        """
        Initialises a TCP network.

        :param options: The options used to configure the TCP connection.
        :param bridge: Bridge object.
        """

        self.__logger = logging.getLogger("VelbusTCP")

        self.__bridge = bridge
        self.__clients = []
        self.__clients_lock = threading.Lock()
        self.__running = False 
        self.__options = options

    def relay(self):
        return self.__options["relay"]

    def host(self):
        return self.__options["host"]

    def port(self):
        return self.__options["port"]        

    def address(self):
        return (self.__options["host"], self.__options["port"])

    def has_ssl(self):
        return self.__options["ssl"] == True

    def has_auth(self):
        return self.__options["auth"] == True

    def __auth_key(self):
        return self.__options["auth_key"]

    def send(self, data, excluded_client=None):
        """
        Sends given data to all connected clients to the network. If excluded_client is supplied, will skip given excluded_client.

        :param data: Specifies what data to send to the connected clients
        :param excluded_client: Specifies which client to skip sending the data to
        """

        assert isinstance(data, bytearray)

        if excluded_client:    
            assert isinstance(excluded_client, Client)

        self.__logger.debug("[TCP OUT] " + " ".join(hex(x) for x in data))

        if self.is_active():
            with self.__clients_lock:
                for client in self.__clients:

                    if client.is_active():

                        try:
                            if (client != excluded_client) and packetexcluder.should_accept(data, client):
                                client.send(data)
                        except:
                            continue

    def __accept_sockets(self):
        """
        Accepts clients from given socket, if the tcp server is closed it will also close socket
        """

        assert isinstance(self.__bind_socket, socket.socket)

        while self.is_active():

            try:
                connection, address = self.__bind_socket.accept()

                # Make sure that we're still active
                if self.is_active():

                    self.__logger.info("TCP connection from {0}".format(str(address)))

                    if self.has_ssl():
                        
                        try:
                            return self.__context.wrap_socket(connection, server_side=True)

                        except ssl.SSLError as e:
                            self.__logger.error("Couldn't wrap socket")
                            raise e

                    client = Client(connection, self.__on_packet_received, self.__on_client_close)

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

    def __on_packet_received(self, client, packet):

        assert isinstance(client, Client)
        assert isinstance(packet, bytearray)

        # Make sure we should accept the packet
        if packetexcluder.should_accept(packet, client):
            self.__bridge.tcp_packet_received(self, client, packet)

    def __on_client_close(self, client):

        assert isinstance(client, Client)

        # Warning message
        if self.__options["auth"] and not client.is_authorized():
            self.__logger.info("TCP connection closed {0} [auth failed]".format(str(client.address())))
        else:
            self.__logger.info("TCP connection closed {0}".format(str(client.address())))

    def is_active(self):
        """
        Returns whether or not the TCP connection is active

        :return: boolean - Whether or not the TCP connection is active
        """

        return self.__running

    def start(self):
        """
        Starts up the TCP server
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
        
        self.__logger.info("Listening to TCP connections on {0}:{1}".format(self.host(), self.port()))

        # Now that we reached here, set running
        self.__running = True

        # Start the server thread to handle connections
        self.__server_thread      = threading.Thread(target=self.__accept_sockets)
        self.__server_thread.name = 'TCP server thread'
        self.__server_thread.start()

    def stop(self):
        """
        Stops the TCP server
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