import logging
from typing import Dict, List, Optional
from velbustcp.lib import consts
from velbustcp.lib.connection.tcp.client import Client
from velbustcp.lib.connection.tcp.events import OnNetworkManagerPacketReceived
from velbustcp.lib.connection.tcp.network import Network
from velbustcp.lib.packet.packetcache import packet_cache


class NetworkManager:

    on_packet_received: Optional[OnNetworkManagerPacketReceived] = None

    def __init__(self) -> None:
        self.__tcp_buffer: Dict[str, Client] = {}
        self.__logger: logging.Logger = logging.getLogger("__main__." + __name__)
        self.__networks: List[Network] = []

    def add_network(self, network: Network):
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
            self.__logger.warning("Buffer full on TCP receive.")
            return

        # Add to cache
        packet_id = packet_cache.add(packet)

        # Add to dict
        self.__tcp_buffer[packet_id] = client

        if self.__logger.isEnabledFor(logging.DEBUG):  # pragma: no cover
            self.__logger.debug("Added request %s to buffer", packet_id)

        if self.on_packet_received:
            self.on_packet_received(packet_id)
