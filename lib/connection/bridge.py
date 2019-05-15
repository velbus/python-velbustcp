import logging
import time

from .bus import Bus
from .network import Network

class Bridge():
    """
    Bridge class for the Velbus-TCP connection.

    Connects serial and TCP connection together.
    """

    def __init__(self, settings):
        """
        Initialises the Bridge class.
        """

        # Logger
        self.__logger = logging.getLogger("VelbusTCP")

        self.__settings = settings

        # Create bus and TCP server
        self.__bus = Bus(options=settings["serial"], bridge=self)
        self.__network = Network(options=settings["tcp"], bridge=self)
        
    def start(self):
        """
        Starts bus and when succesful, starts network.
        """

        while not self.__bus.is_active():

            try:
                self.__bus.start()
            except:
                self.__logger.error("Couldn't create bus connection, waiting 5 seconds")
                time.sleep(5)

        self.__network.start()

    def bus_error(self):
        """
        Called when bus goes into error.

        Closed both bus, then re-opens.
        """

        self.__bus.stop()
        self.start()
    
    def bus_packet_received(self, packet):
        """
        Called when the serial connection receives a packet.

        :param packet: The received packet on the serial connection.
        """

        self.__logger.debug("[BUS IN] " + " ".join(hex(x) for x in packet))

        if (self.__network.is_active()):
            self.__network.send(packet)

    def tcp_packet_received(self, client, packet):
        """
        Called when the TCP server receives a packet from a client.

        :param client: Client which sent the packet
        :param packet: Packet received from the client
        """

        self.__logger.debug("[TCP IN] " + " ".join(hex(x) for x in packet))

        # Relay to other TCP clients?
        if (self.__settings["tcp"]["relay"] and self.__network.is_active()):
            self.__network.send_exclude(packet, client)

        if (self.__bus.is_active()):
            self.__bus.send(packet)

    def stop(self):
        """
        Stops bus and network.
        """

        self.__bus.stop()
        self.__network.stop()