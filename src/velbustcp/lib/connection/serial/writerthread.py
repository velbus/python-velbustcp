from collections import deque
import threading
import time
from typing import Any, Deque, Tuple
from velbustcp.lib import consts
import logging
from velbustcp.lib.connection.serial.serialprotocol import VelbusSerialProtocol
from velbustcp.lib.packet.packetcache import packet_cache


class WriterThread(threading.Thread):

    serial: Any
    protocol: VelbusSerialProtocol

    __send_event: threading.Event
    __send_buffer: Deque[str]
    __serial_lock: threading.Event

    def __init__(self, serial_instance, protocol_factory: VelbusSerialProtocol):
        self.serial = serial_instance
        self.protocol = protocol_factory
        self.__send_event = threading.Event()
        self.__send_buffer = deque()
        self.__logger = logging.getLogger(__name__)
        self.__serial_lock = threading.Event()
        self.unlock()
        threading.Thread.__init__(self)

    def stop(self):
        """Stop the reader thread"""
        self.alive = False
        self.__send_event.set()
        self.join(2)

    def queue(self, packet_id: str):
        self.__send_buffer.append(packet_id)
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

        while self.is_alive() and self.serial.is_open:
            self.__send_event.wait()
            self.__send_event.clear()

            # While we have packets to send
            while len(self.__send_buffer) > 0:

                # Still connected?
                if not self.is_alive() or not self.serial.is_open:
                    break

                packet_id = self.__send_buffer.popleft()
                packet = packet_cache.get(packet_id)

                # Ensure that we don't write to the bus too fast
                delta_time = time.monotonic() - last_send_time
                if delta_time < consts.SEND_DELAY:
                    time.sleep(consts.SEND_DELAY - delta_time)

                # Wait for serial lock to be not set
                self.__serial_lock.wait()

                # Write packet and set new last send time
                try:
                    self.serial.write(packet)

                    if self.protocol.bus_packet_sent:
                        self.protocol.bus_packet_sent(packet_id)

                except Exception as e:
                    self.__logger.exception(e)
                    self.__on_error()

                last_send_time = time.monotonic()