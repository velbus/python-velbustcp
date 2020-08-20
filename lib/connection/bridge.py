import logging
import time
import datetime
import uuid

from .bus import Bus
from .network import Network
from .client import Client
from ..settings import settings_dict
from ..ntp import Ntp

class Bridge():
    """
    Bridge class for the Velbus-TCP connection.

    Connects serial and TCP connection(s) together.
    """

    def __init__(self):
        """
        Initialises the Bridge class.
        """

        self.__settings = settings_dict

        # Logger
        self.__logger = logging.getLogger("VelbusTCP")

        # Create bus
        self.__bus = Bus(options=self.__settings["serial"], bridge=self)
        self.__bus_active = True
        self.__bus_buffer_ready = True

        # Create network connection(s)
        self.__networks = []
        for connection in self.__settings["connections"]:
            self.__networks.append(Network(options=connection, bridge=self))

        # Packet buffer
        self.__buffer = []

        # Sent packets dict
        # [packet_id] = (client, packet)
        self.__received_packets = {}

        # Create NTP
        self.__ntp = Ntp(self.__settings["ntp"], self.send)
        
    def start(self):
        """
        Starts bus and when succesful, starts TCP network(s).
        """

        while not self.__bus.is_active():

            try:
                self.__bus.start()
            except:
                self.__logger.error("Couldn't create bus connection, waiting 5 seconds")
                time.sleep(5)

        for network in self.__networks:
            network.start()

        if self.__settings["ntp"]["enabled"]:
            self.__ntp.start()  

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

        assert isinstance(packet, bytearray)

        self.__logger.debug("[BUS IN] " + " ".join(hex(x) for x in packet))

        # Buffer full/off?
        has_command = (packet[3] and 0x0F) != 0

        if packet[1] == consts.PRIORITY_HIGH:
            if has_command:

                command = packet[4]
                if command in [consts.COMMAND_BUS_ACTIVE, consts.COMMAND_BUS_OFF, consts.COMMAND_BUS_BUFFERREADY, consts.COMMAND_BUS_BUFFERFULL]:

                    if command == consts.COMMAND_BUS_ACTIVE:
                        self.__logger.info("Received bus active")
                        self.__bus_active = True
                    
                    elif command == consts.COMMAND_BUS_OFF:
                        self.__logger.info("Received bus off")
                        self.__bus_active = False

                    elif command == consts.COMMAND_BUS_BUFFERREADY:
                        self.__logger.info("Received bus buffer ready")
                        self.__bus_buffer_ready = True

                    elif command == consts.COMMAND_BUS_BUFFERFULL:
                        self.__logger.info("Received bus buffer full")
                        self.__bus_buffer_ready = False

        for network in self.__networks:
            if network.is_active():
                network.send(packet)

    def tcp_packet_received(self, network, client, packet):
        """
        Called when a network receives a packet from a client.

        :param network: Network which received the packet
        :param client: Client which sent the packet
        :param packet: Packet received from the client
        """

        assert isinstance(network, Network)
        assert isinstance(client, Client)
        assert isinstance(packet, bytearray)

        #TODO: Only send to network if bus is active?

        self.__logger.debug("[TCP IN] " + " ".join(hex(x) for x in packet))

        # Generate unique ID for this packet
        packet_id = uuid.uuid4()
        
        # Add to dict
        self.__received_packets[packet_id] = (client, packet)
        self.__logger.debug(f"Added {packet_id} to dict.")

        if self.__bus.is_active():
            self.__bus.send((packet_id, packet))

    def bus_packet_sent(id) -> None:
        """
        Called when the bus sent a packet on the serial port.
        
        @id: The id of the packet sent.
        """

        assert isinstance(id, str)

        client, packet = self.__received_packets[id]

        # Relay to connected network clients
        for network in self.__networks:

            # Send to everyone except the one we received it from
            if network != client and network.is_active() and network.relay():
                network.send(packet)

        del self.__received_packets[id]

    def stop(self):
        """
        Stops NTP, bus and network.
        """

        self.__ntp.stop()
        self.__bus.stop()

        for network in self.__networks:
            network.stop()        