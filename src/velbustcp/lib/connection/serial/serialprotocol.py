from typing import Any
import serial
import logging
from velbustcp.lib.packet.packetcache import packet_cache
from velbustcp.lib.packet.packetparser import PacketParser
from velbustcp.lib.connection.serial.events import OnBusPacketReceived, OnBusError, OnBusPacketSent


class VelbusSerialProtocol(serial.threaded.Protocol):
    """Velbus serial protocol.
    """

    bus_packet_received: OnBusPacketReceived
    bus_packet_sent: OnBusPacketSent
    on_error: OnBusError

    def __init__(self):
        self.__logger = logging.getLogger("__main__." + __name__)
        self.__parser = PacketParser()

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self

    def data_received(self, data: bytes):
        """Called upon serial data receive.

        Args:
            data (bytes): Data received from the serial bus.
        """

        if data:
            self.__parser.feed(bytearray(data))

            # Try to get new packets in the parser
            packet = self.__parser.next()

            while packet:

                if self.bus_packet_received:
                    packet_id = packet_cache.add(packet)
                    self.bus_packet_received(packet_id)

                packet = self.__parser.next()

    def connection_lost(self, exc: Exception):
        self.__logger.error("Connection lost")

        if exc:
            self.__logger.exception(exc)

        if self.on_error:
            self.on_error()
