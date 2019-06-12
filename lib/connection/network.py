import threading
import socket
import ssl
import logging
import sys
import os

from .. import packetexcluder, settings
from .client import Client
from .bridge import Bridge

class Network():

    def __init__(self, options, bridge):
        """
        Initialises a TCP network.

        :param options: The options used to configure the TCP connection.
        :param bridge: Bridge object.
        """

        assert isinstance(bridge, Bridge)

        self.__logger = logging.getLogger("VelbusTCP")

        ## Check if provided options are valid

        self.__bridge = bridge
        self.__clients = []
        self.__clients_lock = threading.Lock()
        self.__running = False 
        self.__options = options  

    def relay(self):
        return self.__options["relay"]      

    def send(self, data):
        """
        Sends given data to all connected clients

        :param data: Specifies what data to send to the connected clients
        """

        assert isinstance(data, bytearray)

        self.__logger.debug("[TCP OUT] " + " ".join(hex(x) for x in data))

        if self.is_active():
            with self.__clients_lock:
                for client in self.__clients:

                    if client.is_active():

                        try:
                            if packetexcluder.should_accept(data, client):
                                client.send(data)
                                
                        except:
                            continue


    def send_exclude(self, data, exluded_client):
        """
        Sends given data to all connected clients except the one specified as parameter

        :param data: Specifies what data to send to the connected clients
        :param exluded_client: Specifies which client to skip sending the data to
        """

        assert isinstance(data, bytearray)
        assert isinstance(exluded_client, Client)

        if self.is_active():
            with self.__clients_lock:

                for client in self.__clients:
                   
                    if (client is not exluded_client) and client.is_authenticated() and packetexcluder.should_accept(data, client):
                        try:
                            client.send(data)                        
                        except:
                            continue


    def __accept_sockets(self, binding_socket, ssl=False, authorize=False, authorize_key=""):
        """
        Accepts clients from given socket, if the tcp server is closed it will also close socket
        """

        assert isinstance(binding_socket, socket.socket)

        while self.is_active():

            try:
                connection, address = binding_socket.accept()

                if self.is_active():

                    self.__logger.info("TCP connection from " + str(address))

                    if ssl:
                        
                        try:
                            return self.__context.wrap_socket(connection, server_side=True)

                        except ssl.SSLError as e:
                            self.__logger.error("Couldn't wrap socket")
                            raise e

                    client = Client(connection, self.__on_packet_received, self.__on_client_close)

                    if authorize:
                        client.set_should_authorize(authorize_key)

                    client.start()

                    with self.__clients_lock:
                        self.__clients.append(client)                   
                
            except Exception as e:
                self.__logger.error("Couldn't accept socket")
                self.__logger.exception(str(e))     
           
        binding_socket.close()
        self.__logger.info("Closed TCP socket")

    def __on_packet_received(self, client, packet):

        assert isinstance(client, Client)
        assert isinstance(packet, bytearray)

        # Make sure we should accept the packet
        if packetexcluder.should_accept(packet, self):
            self.__bridge.tcp_packet_received(self, client, packet)

    def __on_client_close(self, client):

        assert isinstance(client, Client)

        # Warning message
        if settings.settings["tcp"]["auth"] and not client.is_authenticated():
            self.__logger.info("TCP connection closed " + str(client.address()) + " [auth failed]")
        else:
            self.__logger.info("TCP connection closed " + str(client.address()))       

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
        self.__bind_socket.bind(("", settings.settings["tcp"]["port"]))
        self.__bind_socket.listen(0)

        if settings.settings["tcp"]["ssl"]:
            self.__context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)       
            self.__context.load_cert_chain(settings.settings["tcp"]["cert"], keyfile=settings.settings["tcp"]["pk"])
        
        self.__logger.info("Listening to TCP connections on " + str(settings.settings["tcp"]["port"]))

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

            self.__logger.info("Stopping TCP connection")

            # Set running to false
            self.__running = False

            # Stop every client listening
            with self.__clients_lock:
                for client in self.__clients:
                    client.stop()

            # Connect to itself to stop the blocking accept
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("127.0.0.1", settings.settings["tcp"]["port"]))

            # Wait till the server thread is closed
            self.__server_thread.join()