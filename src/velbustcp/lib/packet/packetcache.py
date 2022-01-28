import uuid
from typing import Dict


class PacketCache:

    __cache: Dict[str, bytearray] = {}

    def add(self, packet: bytearray) -> str:
        """Adds a packet to the cache.

        Args:
            packet (bytearray): A Velbus packet in the form of a bytearray.

        Returns:
            str: Returns an str ID to retrieve it later.
        """
        packet_id = str(uuid.uuid4())
        self.__cache[packet_id] = packet

        return packet_id

    def get(self, packet_id: str) -> bytearray:
        return self.__cache[packet_id]

    def delete(self, packet_id: str) -> None:
        del self.__cache[packet_id]


packet_cache: PacketCache = PacketCache()
