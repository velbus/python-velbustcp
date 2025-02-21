import serial
import serial.threaded
import serial.tools.list_ports
import threading
import logging
from velbustcp.lib.packet.handlers.busstatus import BusStatus
from velbustcp.lib.settings.serial import SerialSettings
from velbustcp.lib.connection.serial.factory import construct_serial_obj, find_port
from velbustcp.lib.connection.serial.serialprotocol import VelbusSerialProtocol
from velbustcp.lib.connection.serial.writerthread import WriterThread
from velbustcp.lib.signals import on_bus_receive, on_bus_fault


class Bus():

    def __init__(self, options: SerialSettings):
        """Initialises a bus connection.

        Args:
            options (dict): The options used to configure the serial connection.
        """

        # Hook signals
        def handle_on_bus_receive(sender, **kwargs):
            old_state = self.__bus_status.alive
            packet = kwargs["packet"]
            self.__bus_status.receive_packet(packet)

            if old_state == self.__bus_status.alive:
                return

            if self.__bus_status.active:
                self.__writer.unlock()
            else:
                self.__writer.lock()
        self.handle_on_bus_receive = handle_on_bus_receive
        on_bus_receive.connect(handle_on_bus_receive)

        def handle_on_bus_fault(sender, **kwargs):
            self.stop()
            self.ensure()
        self.handle_on_bus_fault = handle_on_bus_fault
        on_bus_fault.connect(handle_on_bus_fault)

        self.__logger = logging.getLogger("__main__." + __name__)
        self.__reconnect_event = threading.Event()
        self.__options = options

        self.__bus_status: BusStatus = BusStatus()

        self.__do_reconnect: bool = False
        self.__connected: bool = False

    def __reconnect(self) -> None:
        """Reconnects until active.
        """

        self.__logger.info("Attempting to connect")

        while self.__do_reconnect and not self.is_active():
            try:
                self.__start()
            except Exception:
                self.__logger.exception("Couldn't create bus connection, waiting 5 seconds")
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

        # Already active
        if self.is_active():
            return

        # Already trying to connect
        if self.__do_reconnect:
            return

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

        serial_port = construct_serial_obj(self.__port)

        if not serial_port.isOpen():
            raise Exception("Couldn't open port {0}".format(self.__port))

        # Now that we're connected, set connected state
        self.__connected = True

        # Create reader thread
        self.__reader = serial.threaded.ReaderThread(serial_port, VelbusSerialProtocol())
        self.__reader.start()

        # Create write thread
        self.__writer = WriterThread(serial_port)
        self.__writer.start()

        self.__serial_port = serial_port 

        self.__logger.info("Serial connection active on port %s", self.__port)

    def stop(self) -> None:
        """Stops the serial communication if the serial connection is active.
        """

        if not self.is_active():
            return

        self.__logger.info("Stopping serial connection")

        self.__do_reconnect = False
        self.__connected = False
        self.__reconnect_event.set()

        if self.__reader and self.__reader.alive:
            self.__reader.close()

        if self.__writer and self.__writer.alive:
            self.__writer.close()

        if self.__serial_port.isOpen():
            self.__serial_port.close()

    def send(self, packet: bytearray) -> None:
        """Queues a packet to be sent on the serial connection.

        Args:
            packet (bytearray): An id
        """

        if self.is_active():
            self.__writer.queue(packet)
