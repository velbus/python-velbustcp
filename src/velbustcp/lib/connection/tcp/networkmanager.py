import logging
from typing import Dict, List
from velbustcp.lib import consts
from velbustcp.lib.connection.tcp.client import Client
from velbustcp.lib.connection.tcp.events import OnNetworkManagerPacketReceived
from velbustcp.lib.connection.tcp.network import Network
from velbustcp.lib.packet.packetcache import packet_cache
from velbustcp.lib.settings.network import NetworkSettings


class NetworkManager:

    __logger: logging.Logger
    __networks: List[Network] = []

    # Buffer to track received TCP packets
    __tcp_buffer: Dict[str, Client] = {}

    on_packet_received: OnNetworkManagerPacketReceived

    def __init__(self, connections: List[NetworkSettings]) -> None:

        self.__tcp_buffer = {}
        self.__logger = logging.getLogger("__main__." + __name__)

        for connection in connections:
            network = Network(options=connection)
            network.on_packet_received = self.__packet_received
            self.__networks.append(network)

    def start(self):

        for network in self.__networks:
            network.start()

    def stop(self):

        for network in self.__networks:
            network.stop()

    def send(self, packet_id: str):

        excluded_client = None

        if packet_id in self.__tcp_buffer:
            excluded_client = self.__tcp_buffer[packet_id]
            del self.__tcp_buffer[packet_id]

        packet = packet_cache.get(packet_id)

        # Send to networks
        for network in self.__networks:
            network.send(packet, excluded_client)

    def __packet_received(self, client: Client, packet: bytearray):
        """Called upon receiving a packet from a Network.

        Args:
            client (Client): Client which sent the packet.
            packet (bytearray): Packet received from the client.
        """

        # Do we not yet have exceeded the max buffer length?
        if len(self.__tcp_buffer) == consts.MAX_BUFFER_LENGTH:
            self.__logger.warn("Buffer full on TCP receive.")
            return

        # Add to cache
        packet_id = packet_cache.add(packet)

        # Add to dict
        self.__tcp_buffer[packet_id] = client

        if self.__logger.isEnabledFor(logging.DEBUG):
            self.__logger.debug("Added request %s to buffer", packet_id)

        if self.on_packet_received:
            self.on_packet_received(packet_id)
