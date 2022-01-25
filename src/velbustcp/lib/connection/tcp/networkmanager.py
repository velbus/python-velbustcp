from typing import Dict, List, Optional, Tuple
from velbustcp.lib import consts
from velbustcp.lib.connection.tcp.client import Client
from velbustcp.lib.connection.tcp.events import OnNetworkManagerPacketReceived, OnNetworkPacketReceived
from velbustcp.lib.connection.tcp.network import Network
from velbustcp.lib.packet.packetcache import packet_cache
from velbustcp.lib.settings.network import NetworkSettings


class NetworkManager:

    __networks: List[Network] = []
    
    # Buffer to track received TCP packets
    __tcp_buffer: Dict[str, Client] = {}
    
    on_packet_received: OnNetworkManagerPacketReceived

    def __init__(self, connections: List[NetworkSettings]) -> None:

        self.__tcp_buffer = {}

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

        # Relay to connected network clients
        for network in self.__networks:

            # Send to everyone except the one we received it from
            if network.is_active() and network.relay():
                network.send(packet, excluded_client)

    def __packet_received(self, client: Client, data: bytearray):
        """Queues a packet to be sent on the bus.

        Args:
            packet (bytearray): Packet received from the client.
            client (Client, optional): Client which sent the packet. Defaults to None.
        """

        # Do we not yet have exceeded the max buffer length?
        if len(self.__tcp_buffer) == consts.MAX_BUFFER_LENGTH:
            self.__logger.warn("Buffer full on TCP receive.")
            return

        # Add to cache
        packet_id = packet_cache.add(data)

        # Add to dict
        self.__tcp_buffer[packet_id] = client

        self.__logger.debug(f"Added request {packet_id} to buffer.")

        if self.on_packet_received:
            self.on_packet_received(packet_id, data)
