import logging
import threading

from .. import settings, packetparser

class Client():


    def __init__(self, address, connection, callback, on_close):
        """
        Initialises a client.
        """

        self.__logger = logging.getLogger("VelbusTCP")

        self.__address = address
        self.__connection = connection
        self.__authenticated = False
        self.__callback = callback
        self.__on_close = on_close

        # Start a thread to handle receive
        self._receive_thread      = threading.Thread(target=self.__recv)
        self._receive_thread.name = 'Receive from client thread'
        self._receive_thread.start()

    def send(self, data):
        """
        Sends data to the client.
        """
        self.__connection.sendall(data)

    def is_authenticated(self):
        """
        @bool
        """

        if settings.settings["tcp"]["auth"]:
            return self.__authenticated

        return True
    
    def address(self):
        return self.__address

    def __recv(self):
        """
        Handles client communication.
        """

        # Handle authentication
        if settings.settings["tcp"]["auth"]:
            auth_key = self.__connection.recv(1024).decode("utf-8").strip()

            if settings.settings["tcp"]["authkey"] == auth_key:
                self.__authenticated = True

        parser = packetparser.PacketParser()

        # Receive data
        while self.is_authenticated():  # and self.is_active():

            print("Recv data")

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

        self.__on_close(self)
        self.__connection.close()