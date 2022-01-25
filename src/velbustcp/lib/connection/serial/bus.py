from typing import  Deque, List, Tuple
import serial
import serial.threaded
import serial.tools.list_ports
import threading
import logging
from velbustcp.lib.settings.serial import SerialSettings
from velbustcp.lib.connection.serial.factory import construct_serial_obj, find_port
from velbustcp.lib.connection.serial.events import OnBusPacketReceived, OnBusPacketSent
from velbustcp.lib.connection.serial.serialprotocol import VelbusSerialProtocol
from velbustcp.lib.connection.serial.writerthread import WriterThread


class Bus():

    __do_reconnect = False
    __connected = False
    __in_error: bool = False
    __protocol: VelbusSerialProtocol

    on_packet_sent: OnBusPacketSent
    on_packet_received: OnBusPacketReceived

    def __init__(self, options: SerialSettings):
        """Initialises a bus connection.

        Args:
            options (dict): The options used to configure the serial connection.
        """

        self.__logger = logging.getLogger(__name__)
        self.__reconnect_event = threading.Event()
        self.__options = options

        self.__protocol = VelbusSerialProtocol()
        self.__protocol.bus_packet_sent = self.__on_packet_sent
        self.__protocol.bus_packet_received = self.__on_packet_received
        self.__protocol.on_error = self.__on_error

    def __on_error(self) -> None:
        """Called when an error occurred.
        """

        self.__in_error = True

        self.stop()
        self.ensure()

    def __reconnect(self) -> None:
        """Reconnects until active.
        """

        self.__logger.info("Attempting to connect")

        while self.__do_reconnect and not self.is_active():
            try:
                self.__start()
            except Exception as e:
                self.__logger.error("Couldn't create bus connection, waiting 5 seconds")
                self.__reconnect_event.clear()
                self.__reconnect_event.wait(5)

    def is_active(self) -> bool:
        """Returns whether or not the serial connection is active.

        Returns:
            bool: A boolean indicating whether or not the serial connection is active.
        """

        return self.__connected

    def ensure(self) -> None:
        """Ensures that a connection with the bus is established.
        """

        if not self.is_active():
            self.__do_reconnect = True

            # Start reconnecting thread
            _ = threading.Thread(target=self.__reconnect)
            _.start()

    def __start(self) -> None:
        """Starts up the serial communication if the serial connection is not yet active.
        """

        if self.is_active():
            return

        self.__port = find_port(options=self.__options)

        if not self.__port:
            raise ValueError("Couldn't find a port to open communication on")

        self.__serial_port = construct_serial_obj(self.__port)

        if not self.__serial_port.isOpen():
            raise Exception("Couldn't open port {0}".format(self.__port))

        # Now that we're connected, set connected state
        self.__connected = True
        self.__in_error = False

        # Create reader thread
        self._reader = serial.threaded.ReaderThread(self.__serial_port, self.__protocol)
        self._reader.start()

        # Create write thread
        self._writer = WriterThread(self.__serial_port, self.__protocol)
        self._writer.start()

        self.__logger.info("Serial connection active on port %s", self.__port)

    def stop(self) -> None:
        """Stops the serial communication if the serial connection is active.
        """

        self.__do_reconnect = False
        self.__reconnect_event.set()

        # Stop serial connection if active
        if self.is_active():
            self.__logger.info("Stopping serial connection")
            self.__connected = False

            if not self.__in_error:
                self._reader.close()

            if self._writer.is_alive():
                self._writer.stop()

    def send(self, packet_id: str) -> None:
        """Queues a packet to be sent on the serial connection.

        Args:
            packet_id (str): An id
        """

        self._writer.queue(packet_id)

    def lock(self) -> None:
        """Locks the bus, disabling writes to the bus.
        """

        self._writer.lock()

    def unlock(self) -> None:
        """Unlocks the bus, allowing writes to the bus.
        """

        self._writer.unlock()

    def __on_packet_received(self, packet: bytearray) -> None:
        """Called when a packet is received from the bus. Propagates it to its callback.

        Args:
            packet (bytearray): The packet that has been received.
        """

        if self.on_packet_received:
            self.on_packet_received(packet)

    def __on_packet_sent(self, packet_id: str) -> None:
        """Called when a packet is sent to the bus. Propagates it to its callback.

        Args:
            packet_id (str): The packet_id that has been sent.
        """

        if self.on_packet_sent:
            self.on_packet_sent(packet_id)
