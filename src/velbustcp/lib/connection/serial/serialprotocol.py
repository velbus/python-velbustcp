from typing import Any
import serial
import logging

from velbustcp.lib.packet.packetparser import PacketParser
from velbustcp.lib.signals import on_bus_receive, on_bus_fault

class VelbusSerialProtocol(serial.threaded.Protocol):
    """Velbus serial protocol.
    """

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

                if self.__logger.isEnabledFor(logging.DEBUG):  # pragma: no cover
                    self.__logger.debug("[BUS IN] %s",  " ".join(hex(x) for x in packet))

                on_bus_receive.send(self, packet=packet)
                packet = self.__parser.next()

    def connection_lost(self, exc: Exception):
        self.__logger.error("Connection lost")

        if exc:
            self.__logger.exception(exc)

        on_bus_fault.send(self)
