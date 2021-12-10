import logging
from typing import List, Optional
import uuid

from velbustcp.lib import consts
from velbustcp.lib.connection.serial.bus import Bus
from velbustcp.lib.connection.tcp.network import Network
from velbustcp.lib.connection.tcp.client import Client
from velbustcp.lib.settings.settings import serial_settings, network_settings, ntp_settings
from velbustcp.lib.ntp.ntp import Ntp


class Bridge():
    """Bridge class for the Velbus-TCP connection.

    Connects serial and TCP connection(s) together.
    """

    __networks: List[Network] = []
    __bus_active = True
    __bus_buffer_ready = True

    def __init__(self):
        """Initialises the Bridge class.
        """

        # Logger
        self.__logger = logging.getLogger(__name__)

        # Create bus
        self.__bus = Bus(options=serial_settings)
        self.__bus.on_packet_received = self.bus_packet_received
        self.__bus.on_packet_sent = self.bus_packet_sent

        # Create network connection(s)
        for connection in network_settings:
            network = Network(options=connection)
            network.on_packet_received = self.tcp_packet_received
            self.__networks.append(network)

        # Buffer to track received TCP packets
        # [packet_id] = (client, packet)
        self.__tcp_buffer = {}

        # Create NTP
        self.__ntp = Ntp(options=ntp_settings)
        self.__ntp.on_packet_send_request = self.send

    def start(self) -> None:
        """Starts bus and TCP network(s).
        """

        self.__bus.ensure()

        for network in self.__networks:
            network.start()

        if ntp_settings.enabled:
            self.__ntp.start()

    def send(self, packet: bytearray) -> None:
        """Sends a packet that has been received internally (e.g. NTP).

        Args:
            packet (bytearray): The packet to be sent.
        """

        self.queue_packet(packet, None)

    def bus_packet_received(self, packet: bytearray) -> None:
        """Called when the serial connection receives a packet.

        Args:
            packet (bytearray): The received packet on the serial connection.
        """

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

                    # Lock/unlock bus
                    if not self.__bus_active or not self.__bus_buffer_ready:
                        self.__logger.warn("Locking the bus!")
                        self.__bus.lock()
                    elif self.__bus_active and self.__bus_buffer_ready:
                        self.__logger.warn("Unlocking the bus!")
                        self.__bus.unlock()

        for network in self.__networks:
            if network.is_active():
                network.send(packet)

    def tcp_packet_received(self, client: Client, packet: bytearray):
        """Called when a network receives a packet from a client.

        Args:
            network (Network): Network which received the packet
            client (Client): Client which sent the packet
            packet (bytearray): Packet received from the client
        """

        self.__logger.debug("[TCP IN] " + " ".join(hex(x) for x in packet))
        self.queue_packet(packet, client)

    def queue_packet(self, packet: bytearray, client: Optional[Client] = None) -> None:
        """Queues a packet to be sent on the bus.

        Args:
            packet (bytearray): Packet received from the client.
            client (Client, optional): Client which sent the packet. Defaults to None.
        """

        # Do we not yet have exceeded the max buffer length?
        if len(self.__tcp_buffer) == consts.MAX_BUFFER_LENGTH:
            self.__logger.warn("Buffer full on TCP receive.")
            return

        # Generate unique ID for this packet
        packet_id = str(uuid.uuid4())

        # Add to dict
        self.__tcp_buffer[packet_id] = (client, packet)
        self.__logger.debug(f"Added request {packet_id} to buffer.")

        if self.__bus.is_active():
            self.__bus.send((packet_id, packet))

    def bus_packet_sent(self, packet_id: str) -> None:
        """Called when the bus sent a packet on the serial port.

        Args:
            id (str): The id of the packet sent.
        """

        client, packet = self.__tcp_buffer[packet_id]

        # Relay to connected network clients
        for network in self.__networks:

            # Send to everyone except the one we received it from
            if network.is_active() and network.relay():
                network.send(packet, client)

        del self.__tcp_buffer[packet_id]

    def stop(self) -> None:
        """Stops NTP, bus and network.
        """

        self.__ntp.stop()
        self.__bus.stop()

        for network in self.__networks:
            network.stop()
