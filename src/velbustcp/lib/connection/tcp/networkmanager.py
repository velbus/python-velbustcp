import logging
from typing import List
import asyncio

from velbustcp.lib.connection.tcp.network import Network


class NetworkManager:

    def __init__(self) -> None:
        self.__logger: logging.Logger = logging.getLogger("__main__." + __name__)
        self.__networks: List[Network] = []

    def add_network(self, network: Network):
        self.__networks.append(network)

    async def start(self):
        """Starts all available networks.
        """

        tasks = [network.start() for network in self.__networks]
        await asyncio.gather(*tasks)

    async def stop(self):
        """Stops all connected networks.
        """

        tasks = [network.stop() for network in self.__networks]
        await asyncio.gather(*tasks)

    async def send(self, packet: bytearray):
        """Sends the given packet to all networks.

        Args:
            packet (bytearray): The packet to send.
        """

        tasks = [network.send(packet) for network in self.__networks]
        await asyncio.gather(*tasks)