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
        self.__buffer_condition = asyncio.Condition()
        self.__locked = False

    async def close(self):
        """Stop the writer thread"""
        self.alive = False
        async with self.__buffer_condition:
            self.__buffer_condition.notify_all()  # Wake up the run loop if waiting

    async def queue(self, packet: bytearray):
        """Add a packet to the send buffer and notify the writer thread."""
        async with self.__buffer_condition:
            self.__send_buffer.append(packet)
            self.__buffer_condition.notify()  # Notify the writer thread that a packet is available

    async def run(self):
        """Coroutine to safely write to the serial port with a delay."""
        loop = asyncio.get_event_loop()
        last_send_time = loop.time()

        try:
            while self.alive:
                async with self.__buffer_condition:
                    # Wait until there is data in the buffer and the thread is unlocked
                    await self.__buffer_condition.wait_for(lambda: self.__send_buffer and not self.__locked)

                # Get the next packet to send
                packet = self.__send_buffer.popleft()

                # Enforce the send delay
                delta_time = loop.time() - last_send_time
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

                last_send_time = loop.time()
        except asyncio.CancelledError:
            self.__logger.info("Writer thread cancelled")
        except Exception as e:
            self.__logger.exception("Unexpected error in writer thread: %s", e)

    def lock(self):
        """Locks the writer thread to prevent sending packets."""
        self.__locked = True

    def unlock(self):
        """Unlocks the writer thread to allow sending packets."""
        self.__locked = False
        asyncio.create_task(self.__notify_condition())

    async def __notify_condition(self):
        """Helper coroutine to notify the condition variable."""
        async with self.__buffer_condition:
            self.__buffer_condition.notify()