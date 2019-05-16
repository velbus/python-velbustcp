import threading
import socket
import ssl
import logging
import sys
import os

from .. import packetparser
from .. import packetexcluder

class Network():

    def __init__(self, options, bridge):
        """
        Initialises a TCP network.

        :param options: The options used to configure the TCP connection.
        :param bridge: Bridge object.
        """

        self.__logger = logging.getLogger("VelbusTCP")

        ## Check if provided options are valid

        # Port
        if not "port" in options:
            raise ValueError("No port provided")

        self.__port = int(options["port"])
        
        if (not (self.__port > 0 and self.__port < 65535)):
            raise ValueError("The provided port is invalid {0}".format(self.__port))

        # SSL
        if "ssl" in options:

            # SSL enabled/disabled
            if (options["ssl"] != True) and (options["ssl"] != False):
                raise ValueError("Provided option ssl is invalid {0}".format(options["ssl"]))

            self.__ssl = options["ssl"]

            if self.__ssl:

                # PK
                if (not "pk" in options) or (options["pk"] == "") or (not os.path.isfile(options["pk"])):
                    raise ValueError("Provided private key not found or non given while SSL is enabled")

                # Certificate
                if (not "cert" in options) or (options["cert"] == "") or (not os.path.isfile(options["cert"])):
                    raise ValueError("Provided certificate not found or non given while SSL is enabled")

                self.__pk = options["pk"]
                self.__cert = options["cert"]                

        else:
            self.__ssl = False

        # Auth
        if "auth" in options:

            # Auth enabled/disabled
            if (options["auth"] != True) and (options["auth"] != False):
                raise ValueError("Provided option auth is invalid {0}".format(options["auth"]))

            self.__auth = options["auth"]

            if self.__auth:

                if not ("auth_key" in options) or (options["auth_key"] == ""):
                    raise ValueError("No auth key provided or is empty")

                self.__auth_key = options["auth_key"]

        else:
            self.__auth = False


        self.__bridge = bridge
        self.__clients           = dict()
        self.__clients_lock      = threading.Lock()
        self.__running = False 
        self.__options = options
        

    def send(self, bytes):
        """
        Sends given bytes to all connected clients

        :param bytes: Specifies what bytes to send to the connected clients
        """

        if self.is_active():
            with self.__clients_lock:
                for connection in self.__clients:

                    if self.__clients[connection]["authenticated"]:

                        try:
                            if packetexcluder.should_accept(bytes, self.__clients[connection]):
                                connection.sendall(bytes)
                                self.__logger.debug("[TCP OUT] " + " ".join(hex(x) for x in bytes))
                        except:
                            break


    def send_exclude(self, bytes, client):
        """
        Sends given bytes to all connected clients except the one specified as parameter

        :param bytes: Specifies what bytes to send to the connected clients
        :param client: Specifies which client to skip sending the bytes to
        """

        if self.is_active():
            with self.__clients_lock:

                for connection in self.__clients:
                   
                    if (connection is not client):
                        if self.__clients[connection]["authenticated"]:

                            try:
                                if packetexcluder.should_accept(bytes, self.__clients[connection]):
                                    connection.sendall(bytes)
                            except:
                                break


    def __accept_sockets(self):
        """
        Creates a socket and accepts clients, if the tcp server is closed it will also close socket
        """

        while self.is_active():
            try:

                conn = None
                ssock, address = self.__bind_socket.accept()

                if self.__ssl:
                    try:
                        conn = self.__context.wrap_socket(ssock, server_side=True)
                    except ssl.SSLError as e:
                        self.__logger.error("Couldn't wrap socket")
                        self.__logger.exception(str(e))

                else:
                    conn = ssock
                
            except Exception as e:
                self.__logger.error("Couldn't accept socket")
                self.__logger.exception(str(e))

            if conn:
                self.__logger.info("TCP connection from " + str(address))

                # Add the connection to the connected clients set
                with self.__clients_lock:
                    self.__clients[conn] = {
                        "address": address,
                        "authenticated": False if self.__auth else True,
                    }

                # Start up a new client thread to handle the client communication
                client_thread       = threading.Thread(target=self.__handle_client, args=(conn,))
                client_thread.name  = 'TCP client thread'
                client_thread.start()

        # Call an explicit shutdown on all connected clients
        # This will cancel their recv methods
        with self.__clients_lock:
            for c in self.__clients:
                c.shutdown(socket.SHUT_RDWR)

        self.__bind_socket.close()
        self.__logger.info("Closed TCP socket")

    def __handle_client(self, conn):
        """
        Handles client communication

        @param conn: The connection to handle
        """

        parser = packetparser.PacketParser()

        # Handle authentication
        print("Should auth: " + str(self.__auth))
        if self.__auth:
            auth_key = conn.recv(1024).decode("utf-8").strip()

            if self.__auth_key == auth_key:
                self.__clients[conn]["authenticated"] = True

        # Receive data
        while self.__clients[conn]["authenticated"] and self.is_active():

            print("Recv data")

            try:
                data = conn.recv(1024)

                # If program gets here without data, the client disconnected
                if not data:
                    break

                parser.feed(bytearray(data))
                packet = parser.next()
                while packet is not None:

                    # Make sure we should accept the packet
                    if packetexcluder.should_accept(packet, self.__clients[conn]):
                        self.__bridge.tcp_packet_received(conn, packet)
                    
                    packet = parser.next()

            except Exception as e:
                self.__logger.exception(str(e))
                break

        address = self.__clients[conn]

        # Warning message
        if not self.__clients[conn]["authenticated"]:
            self.__logger.info("TCP connection closed " + str(address) + " [auth failed]")
        else:
            self.__logger.info("TCP connection closed " + str(address))                

        # Remove the connection from the connected clients set
        with self.__clients_lock:
            del self.__clients[conn]

        conn.close()

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
        self.__bind_socket.bind(("", self.__port))
        self.__bind_socket.listen(0)

        if self.__ssl:
            self.__context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)       
            self.__context.load_cert_chain(self.__cert, keyfile=self.__pk)
        
        self.__logger.info("Listening to TCP connections on " + str(self.__port))

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

            # Connect to itself to stop the blocking accept
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect(("127.0.0.1", self.__port))

            # Wait till the server thread is closed
            self.__server_thread.join()