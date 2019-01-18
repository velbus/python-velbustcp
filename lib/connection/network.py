import threading
import socket
import logging
import sys

from .. import packetparser
from .. import packetexcluder

class Network():

    def __init__(self, options, bridge):
        """
        Initialises an TCP network.

        :param options: The options used to configure the TCP connection.
        :param bridge: Bridge object.
        """

        self.__logger = logging.getLogger("VelbusTCP")

        # Check if options are valid
        self.__port = int(options["port"])

        if (not (self.__port > 0 and self.__port < 65535)):
            raise ValueError("The provided port is invalid {0}".format(options["port"]))

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
                for c in self.__clients:
                    try:
                        if packetexcluder.should_accept(bytes, self.__clients[c]):
                            c.sendall(bytes)
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
                for c in self.__clients:
                    if (c is not client):
                        try:
                            if packetexcluder.should_accept(bytes, self.__clients[c]):
                                c.sendall(bytes)
                        except:
                            break


    def __accept_sockets(self):
        """
        Creates a socket and accepts clients, if the tcp server is closed it will also close socket
        """

        while self.is_active():
            try:
                (conn, address) = self.__socket.accept()
            except:
                break

            if self.is_active():
                self.__logger.info("TCP connection from " + str(address))

                # Add the connection to the connected clients set
                with self.__clients_lock:
                    self.__clients[conn] = address

                # Start up a new client thread to handle the client communication
                client_thread       = threading.Thread(target=self.__handle_client, args=(conn,))
                client_thread.name  = 'TCP client thread'
                client_thread.start()

        # Call an explicit shutdown on all connected clients
        # This will cancel their recv methods
        with self.__clients_lock:
            for c in self.__clients:
                c.shutdown(socket.SHUT_RDWR)

        self.__socket.close()
        self.__logger.info("Closed TCP socket")

    def __handle_client(self, conn):
        """
        Handles client communication

        @param conn: The connection to handle
        """

        parser = packetparser.PacketParser()

        while self.is_active():
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

        # Remove the connection from the connected clients set
        address = self.__clients[conn]
        with self.__clients_lock:
            del self.__clients[conn]

        conn.close()

        self.__logger.info("TCP connection closed " + str(address))

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
        
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.__socket.bind(("", self.__port))
        #try:
        #   

        #except socket.error as msg:
        #    self.__logger.error("Could not bind to port {0}".format(self.__port))
        #    self.__logger.error(msg)
         #   sys.exit(1)  
        
        self.__socket.listen(0)
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