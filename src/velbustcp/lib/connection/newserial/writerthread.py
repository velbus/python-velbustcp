import asyncio
from collections import deque
from typing import Deque
import logging

from velbustcp.lib import consts
from velbustcp.lib.signals import on_bus_send

class WriterThread:
    def __init__(self, serial_instance: asyncio.StreamWriter):
        self.alive: bool = True
        self.__serial = serial_instance
        self.__logger = logging.getLogger("__main__." + __name__)
        self.__send_buffer: Deque[bytearray] = deque()
        self.__serial_lock = asyncio.Lock()
        self.__locked = False

    async def close(self):
        """Stop the writer thread"""
        self.alive = False

    async def queue(self, packet: bytearray):
        self.__send_buffer.append(packet)

    async def run(self):
        """Coroutine to safely write to the serial port with a delay."""
        last_send_time = asyncio.get_event_loop().time()

        try:
            while self.alive:
                if not self.__send_buffer or self.__locked:
                    await asyncio.sleep(0.1)
                    continue

                packet = self.__send_buffer.popleft()

                delta_time = asyncio.get_event_loop().time() - last_send_time
                if delta_time < consts.SEND_DELAY:
                    await asyncio.sleep(consts.SEND_DELAY - delta_time)

                async with self.__serial_lock:
                    try:
                        if self.__logger.isEnabledFor(logging.DEBUG):
                            self.__logger.debug("[BUS OUT] %s", " ".join(hex(x) for x in packet))

                        self.__serial.write(packet)
                        on_bus_send.send(self, packet=packet)
                    except Exception as e:
                        self.__logger.exception(e)

                last_send_time = asyncio.get_event_loop().time()
        except e:
            self.__logger.info("Writer thread cancelled")

    def lock(self):
        """Locks the writer thread to prevent sending packets."""
        self.__locked = True

    def unlock(self):
        """Unlocks the writer thread to allow sending packets."""
        self.__locked = False