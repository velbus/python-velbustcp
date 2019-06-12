import logging
import threading
import socket

from .. import packetparser

class Client():

    def __init__(self, connection, callback, on_close):
        """
        Initialises a client.
        """

        assert isinstance(connection, socket.socket)
        assert callable(callback)
        assert callable(on_close)        

        self.__logger = logging.getLogger("VelbusTCP")

        self.__connection = connection
        self.__callback = callback
        self.__on_close = on_close

        # Authorization details
        self.__should_authorize = False
        self.__authorized = False
        self.__authorize_key = ""
        
        self.__is_active = False

    def start(self):
        """
        Starts the client to receive.
        """

        # Start a thread to handle receive
        self._receive_thread      = threading.Thread(target=self.__recv)
        self._receive_thread.name = 'Receive from client thread'
        self._receive_thread.start()        

    def stop(self):
        """
        Stops the client to receive
        """     

        if self.is_active():
            self.__is_active = False
            self.__connection.shutdown(socket.SHUT_RDWR)
            self.__connection.close()

            self.__on_close(self)


    def send(self, data):
        """
        Sends data to the client.
        """

        self.__connection.sendall(data)

    def set_should_authorize(self, authorize_key):
        """
        Flags the client so that the client must authorize first before sending messages to the server.
        """

        self.__authorize_key = authorize_key
        self.__should_authorize = True

    def is_authorized(self):
        """
        Whether or not the client is authorized to send messages to the server.
        """

        if not self.__should_authorize:
            return True
        
        else:
            return self.__authorized
    
    def is_active(self):
        return self.__is_active
    
    def address(self):
        """
        Address of the client.
        """

        return self.__connection.getpeername()

    def __recv(self):
        """
        Handles client communication.
        """

        parser = packetparser.PacketParser()

        # Handle authorization
        if self.__should_authorize:
            auth_key = self.__connection.recv(1024).decode("utf-8").strip()

            if self.__authorize_key == auth_key:
                self.__authorized = True

        self.__is_active = True      

        # Receive data
        while self.is_authorized() and self.is_active():

            try:
                data = self.__connection.recv(1024)

                # If program gets here without data, the client disconnected
                if not data:
                    break

                parser.feed(bytearray(data))
                packet = parser.next()
                while packet is not None:
                    self.__callback(self, packet)
                    
                    packet = parser.next()

            except Exception as e:
                self.__logger.exception(str(e))
                break

        self.stop()