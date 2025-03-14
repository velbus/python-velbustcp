import asyncio
import logging

from velbustcp.lib.packet.packetparser import PacketParser
from velbustcp.lib.signals import on_bus_receive, on_bus_fault


class VelbusSerialProtocol(asyncio.Protocol):
    """Velbus serial protocol."""

    def __init__(self):
        self.__logger = logging.getLogger("__main__." + __name__)
        self.__parser = PacketParser()

    def connection_made(self, transport):
        self.transport = transport

    def data_received(self, data: bytes):
        """Called upon serial data receive."""
        if data:
            packets = self.__parser.feed(bytearray(data))
            for packet in packets:
                if self.__logger.isEnabledFor(logging.DEBUG):
                    self.__logger.debug("[BUS IN] %s", " ".join(hex(x) for x in packet))
                on_bus_receive.send(self, packet=packet)

    def connection_lost(self, exc):
        self.__logger.error("Connection lost")
        if exc:
            self.__logger.exception(exc)
        on_bus_fault.send(self)