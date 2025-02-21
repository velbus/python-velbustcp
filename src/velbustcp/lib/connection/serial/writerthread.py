from collections import deque
from serial import Serial
import threading
import time
from typing import Deque
import logging

from velbustcp.lib import consts
from velbustcp.lib.signals import on_bus_send


class WriterThread(threading.Thread):

    def __init__(self, serial_instance: Serial):
        self.alive: bool = False
        self.__serial: Serial = serial_instance
        self.__logger = logging.getLogger("__main__." + __name__)
        self.__send_event: threading.Event = threading.Event()
        self.__send_buffer: Deque[bytearray] = deque()
        self.__serial_lock: threading.Event = threading.Event()
        self.unlock()

        threading.Thread.__init__(self)

    def close(self):
        """Stop the reader thread"""

        if not self.alive:
            return

        self.alive = False
        self.__send_event.set()
        self.join(2)

    def queue(self, packet: bytearray):
        self.__send_buffer.append(packet)
        self.__send_event.set()

    def lock(self) -> None:
        """Locks the write thread.
        """
        self.__serial_lock.clear()

    def unlock(self) -> None:
        """Unlocks the write thread.
        """
        self.__serial_lock.set()

    def run(self) -> None:
        """Thread to safely write to the serial port with a delay.
        """

        last_send_time = time.monotonic()
        self.alive: bool = True

        while self.alive and self.__serial.is_open:
            self.__send_event.wait()
            self.__send_event.clear()

            # While we have packets to send
            while len(self.__send_buffer) > 0:

                # Still connected?
                if not self.alive or not self.__serial.is_open:
                    return

                packet = self.__send_buffer.popleft()

                # Ensure that we don't write to the bus too fast
                delta_time = time.monotonic() - last_send_time
                if delta_time < consts.SEND_DELAY:
                    time.sleep(consts.SEND_DELAY - delta_time)

                # Wait for serial lock to be not set
                self.__serial_lock.wait()

                # Write packet and set new last send time
                try:
                    if self.__logger.isEnabledFor(logging.DEBUG):
                        self.__logger.debug("[BUS OUT] %s",  " ".join(hex(x) for x in packet))

                    self.__serial.write(packet)
                    on_bus_send.send(self, packet=packet)

                except Exception as e:
                    self.__logger.exception(e)
                    # self.__on_error()

                last_send_time = time.monotonic()
