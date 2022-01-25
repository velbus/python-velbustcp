


import uuid
from typing import Dict


class PacketCache:

    __cache: Dict[str, bytearray]

    def add(self, packet: bytearray) -> str:
        
        # Generate unique ID for this packet
        packet_id = str(uuid.uuid4())

        self.__cache[packet_id] = packet

    def get(self, packet_id: str) -> bytearray:
        return self.__cache[packet_id]

    def delete(self, packet_id: str) -> None:
        del self.__cache[packet_id]

packet_cache: PacketCache = PacketCache()
