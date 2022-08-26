import logging
from typing import List

from velbustcp.lib.connection.tcp.network import Network


class NetworkManager:

    def __init__(self) -> None:
        self.__logger: logging.Logger = logging.getLogger("__main__." + __name__)
        self.__networks: List[Network] = []

    def add_network(self, network: Network):
        self.__networks.append(network)

    def start(self):
        """Starts all available networks.
        """

        for network in self.__networks:
            network.start()

    def stop(self):
        """Stops all connected networks.
        """

        for network in self.__networks:
            network.stop()

    def send(self, packet: bytearray):
        """Sends the given packet to all networks.

        Args:
            packet (bytearray): The packet to send.
        """

        for network in self.__networks:
            network.send(packet)
