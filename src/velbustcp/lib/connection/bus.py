from typing import Any, Deque, List, Protocol, Tuple
import serial
import serial.threaded
import serial.tools.list_ports
import threading
import collections
import time
import logging

from velbustcp.lib.packet.packetparser import PacketParser
from velbustcp.lib import consts
from velbustcp.lib.settings.serial import SerialSettings

SEND_DELAY = 0.05  # The minimum required time between consecutive bus writes, in seconds
READ_DELAY = 0.01

PRODUCT_IDS = ['VID:PID=10CF:0B1B', 'VID:PID=10CF:0516', 'VID:PID=10CF:0517', 'VID:PID=10CF:0518']


class OnBusPacketReceived(Protocol):
    def __call__(self, packet: bytearray) -> None:
        pass


class OnBusError(Protocol):
    def __call__(self) -> None:
        pass


class VelbusSerialProtocol(serial.threaded.Protocol):
    """Velbus serial protocol.
    """

    bus_packet_received: OnBusPacketReceived
    on_error: OnBusError

    def __init__(self):
        self.__logger = logging.getLogger(__name__)
        self.__parser = PacketParser()

    def __call__(self, *args: Any, **kwds: Any) -> Any:
        return self

    def data_received(self, data: bytes):
        """Called upon serial data receive.

        Args:
            data (bytes): Data received from the serial bus.
        """

        if data:
            self.__logger.debug(bytearray(data))
            self.__parser.feed(bytearray(data))

            # Try to get new packets in the parser
            packet = self.__parser.next()

            while packet:

                if self.bus_packet_received:
                    self.bus_packet_received(packet)

                packet = self.__parser.next()

    def connection_lost(self, exc: Exception):
        self.__logger.error("Connection lost")

        if exc:
            self.__logger.exception(exc)

        if self.on_error:
            self.on_error()


class OnBusPacketSent(Protocol):
    def __call__(self, packet_id: str) -> None:
        pass


class Bus():

    __do_reconnect = False
    __connected = False
    __in_error = False
    __send_buffer: Deque[Tuple[str, bytearray]]

    on_packet_sent: OnBusPacketSent
    on_packet_received: OnBusPacketReceived

    def __init__(self, options: SerialSettings):
        """Initialises a bus connection.

        Args:
            options (dict):The options used to configure the serial connection.
        """

        self.__logger = logging.getLogger(__name__)

        self.__reconnect_event = threading.Event()
        self.__send_event = threading.Event()
        self.__send_buffer = collections.deque(maxlen=consts.MAX_BUFFER_LENGTH)

        # Serial lock event
        self.__serial_lock = threading.Event()
        self.unlock()

        self.__options = options

    def __write_thread(self) -> None:
        """Thread to safely write to the serial port with a delay.
        """

        last_send_time = time.monotonic()

        while self.is_active() and not self.in_error():
            self.__send_event.wait()
            self.__send_event.clear()

            # While we have packets to send
            while len(self.__send_buffer) > 0:

                # Still connected?
                if not self.is_active():
                    break

                packet_id, packet = self.__send_buffer.popleft()

                # Ensure that we don't write to the bus too fast
                delta_time = time.monotonic() - last_send_time
                if delta_time < SEND_DELAY:
                    time.sleep(SEND_DELAY - delta_time)

                # Wait for serial lock to be not set
                self.__serial_lock.wait()

                # Write packet and set new last send time
                try:
                    self.__serial_port.write(packet)

                    if self.on_packet_sent:
                        self.on_packet_sent(packet_id)

                    self.__logger.debug("[BUS OUT] " + " ".join(hex(x) for x in packet))
                except Exception as e:
                    self.__logger.exception(e)
                    self.__on_error()

                last_send_time = time.monotonic()

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
                self.start()
            except Exception:
                self.__logger.error("Couldn't create bus connection, waiting 5 seconds")
                self.__reconnect_event.clear()
                self.__reconnect_event.wait(5)

    def __search_for_serial(self) -> List[str]:
        """Searches the connected serial list for an eligible device.

        Returns:
            List[str]: A list of strings containing the port(s) on which a connection is possible.
        """

        devices = []

        for port in serial.tools.list_ports.comports():
            try:
                # Found, try open it first
                if any(product_id in port.hwid for product_id in PRODUCT_IDS):
                    try_open_port = serial.Serial(port=port.device)
                    try_open_port.close()
                    devices.append(port.device)

            except Exception:
                pass

        return devices

    def is_active(self) -> bool:
        """Returns whether or not the serial connection is active.

        Returns:
            bool: A boolean indicating whether or not the serial connection is active.
        """

        return self.__connected

    def in_error(self) -> bool:
        """Returns whether or not the serial connection is in error.

        Returns:
            bool: A boolean indicating whether or not the serial connection is in error.
        """

        return self.__in_error

    def ensure(self) -> None:
        """Ensures that a connection with the bus is established.
        """

        if not self.is_active():
            self.__do_reconnect = True

            # Start reconnecting thread
            _ = threading.Thread(target=self.__reconnect)
            _.start()

    def start(self) -> None:
        """Starts up the serial communication if the serial connection is not yet active.
        """

        if self.is_active():
            return

        self.__port = None

        # If we need to autodiscover port
        if self.__options.autodiscover:

            ports = self.__search_for_serial()

            if len(ports) > 0:
                self.__logger.info("Autodiscovered {0} port(s): {1}".format(len(ports), ports))
                self.__logger.info("Choosing {0}".format(ports[0]))
                self.__port = ports[0]

            else:
                self.__port = self.__options.port

        # No need to autodiscover, take given port
        else:
            self.__port = self.__options.port

        if self.__port is None or self.__port == '':
            raise ValueError("Couldn't find a port to open communication on")

        self.__serial_port = serial.Serial(
            port=self.__port,
            baudrate=38400,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
            bytesize=serial.EIGHTBITS,
            xonxoff=0,
            timeout=None,
            dsrdtr=0,
            rtscts=0,
        )

        if not self.__serial_port.isOpen():
            raise Exception("Couldn't open port {0}".format(self.__port))

        # Now that we're connected, set connected state
        self.__connected = True
        self.__in_error = False

        # Create reader thread
        protocol = VelbusSerialProtocol()
        protocol.bus_packet_received = self.__on_packet_received
        protocol.on_error = self.__on_error
        self._reader = serial.threaded.ReaderThread(self.__serial_port, protocol)
        self._reader.start()

        # Create write thread
        self.__send_thread = threading.Thread(target=self.__write_thread)
        self.__send_thread.daemon = True
        self.__send_thread.name = 'Serial writing thread'
        self.__send_thread.start()

        self.__logger.info("Serial connection active on port {0}".format(self.__port))

    def stop(self) -> None:
        """Stops the serial communication if the serial connection is active.
        """

        self.__logger.info("Stopping serial connection")

        self.__do_reconnect = False
        self.__reconnect_event.set()

        # Stop serial connection if active
        if self.is_active():
            self.__connected = False

            if not self.in_error():
                self._reader.close()

            self.__send_event.set()
            self.__send_thread.join()

    def send(self, id_packet_tuple: Tuple[str, bytearray]) -> None:
        """Queues a packet to be sent on the serial connection.

        Args:
            id_packet_tuple (Tuple[str, bytearray]): A tuple containing a request ID (str) and data (bytearray)
        """

        self.__send_buffer.append(id_packet_tuple)
        self.__send_event.set()

    def lock(self) -> None:
        """Locks the bus, disabling writes to the bus.
        """

        self.__serial_lock.clear()

    def unlock(self) -> None:
        """Unlocks the bus, allowing writes to the bus.
        """

        self.__serial_lock.set()

    def __on_packet_received(self, packet: bytearray) -> None:
        """Called when a packet is received from the bus. Propagates it to its callback.

        Args:
            packet (bytearray): The packet that has been received.
        """

        if self.on_packet_received:
            self.on_packet_received(packet)
