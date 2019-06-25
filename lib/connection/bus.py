import serial
import serial.threaded
import serial.tools.list_ports
import threading
import collections
import time
from datetime import datetime
import logging
import traceback

from .. import packetparser

SEND_DELAY  = 0.05
READ_DELAY  = 0.01

PRODUCT_IDS = ['VID:PID=10CF:0B1B', 'VID:PID=10CF:0516', 'VID:PID=10CF:0517', 'VID:PID=10CF:0518']

class VelbusSerialProtocol(serial.threaded.Protocol):
    """
    Velbus serial protocol.
    """

    def __init__(self):
        self.__parser = packetparser.PacketParser()

    def data_received(self, data):
        # pylint: disable-msg=E1101
        
        if data:
            self.__parser.feed(bytearray(data))

            # Try to get new packets in the parser
            packet = self.__parser.next()

            while packet:
                self.bridge.bus_packet_received(packet)   
                packet = self.__parser.next()

    def connection_lost(self, exc):
        # pylint: disable-msg=E1101

        if exc is not None:
            print(exc)
            traceback.print_exc(exc)
            self.on_error()

class Bus():

    def __init__(self, options, bridge):
        """
        Initialises a bus connection.

        :param options: The options used to configure the serial connection.
        :param bridge: Bridge object.
        """

        self.__logger = logging.getLogger("VelbusTCP")

        self.__connected = False
        self.__in_error = False
        self.__send_event = threading.Event()
        self.__send_buffer = collections.deque(maxlen=10000)
               
        self.__options = options
        self.__bridge = bridge

    def __write_thread(self):
        """
        Thread to safely write to the serial port with a delay.
        """

        last_send_time = datetime.now()

        while self.is_active() and not self.in_errror():
            self.__send_event.wait()
            self.__send_event.clear()

            # While we have packets to send
            while len(self.__send_buffer) > 0:

                # Still connected?
                if not self.is_active():
                    break

                packet = self.__send_buffer.popleft()

                # Ensure that we sleep SEND_DELAY
                t = datetime.now() - last_send_time
                if t.total_seconds() < SEND_DELAY:
                    q = SEND_DELAY - t.total_seconds()
                    time.sleep(q)

                # Write packet and set new last send time
                try:
                    self.__serial_port.write(packet)
                    self.__logger.debug("[BUS OUT] " + " ".join(hex(x) for x in packet))
                except Exception as e:
                    self.__logger.exception(e)
                    self.__on_error()

                last_send_time = datetime.now()

    def __on_error(self):
        """
        Called when an error occurred.
        """

        self.__in_error = True

    def __search_for_serial(self):
        """
        Searches the connected serial list for an eligible device.

        :return: An array of strings containing the port(s) on which a connection is possible.
        """

        devices = []

        for port in serial.tools.list_ports.comports():
            try:                
                # Found, try open it first
                if any(product_id in port.hwid for product_id in PRODUCT_IDS):
                    try_open_port = serial.Serial(port=port.device)
                    try_open_port.close()
                    devices.append(port.device)

            except Exception as e:
                pass

        return devices

    def is_active(self):
        """
        Returns whether or not the serial connection is active.

        :return: A boolean indicating whether or not the serial connection is active.
        """

        return self.__connected

    def in_errror(self):
        """
        Returns whether or not the serial connection is in error.

        :return: A boolean indicating whether or not the serial connection is in error.
        """

        return self.__in_error

    def start(self):
        """
        Starts up the serial communication if the serial connection is not yet active.
        """

        if self.is_active():
            return

        # If we need to autodiscover port
        if self.__options["autodiscover"]:
           
            ports = self.__search_for_serial()
            
            if len(ports) > 0:
                self.__logger.info("Autodiscovered {0} port(s): {1}".format(len(ports), ports))
                self.__logger.info("Choosing {0}".format(ports[0]))
                self.__port = ports[0]
                
            else:
                self.__port = self.__options["port"]

        # No need to autodiscover, take given port
        else:
            self.__port = self.__options["port"]

        if self.__port is None:
            raise ValueError("Couldn't find a port to open communication on")

        self.__serial_port = serial.Serial(
            port        = self.__port,
            baudrate    = 38400,
            parity      = serial.PARITY_NONE,
            stopbits    = serial.STOPBITS_ONE,
            bytesize    = serial.EIGHTBITS,
            xonxoff     = 0,
            timeout     = None,
            dsrdtr      = 0,
            rtscts      = 0,
        )

        if not self.__serial_port.isOpen():
            raise Exception("Couldn't open port {0}".format(self.__port))

        # Now that we're connected, set connected state
        self.__connected = True
        self.__in_error = False
       
        # Create reader thread
        self._reader = serial.threaded.ReaderThread(self.__serial_port, VelbusSerialProtocol)
        self._reader.start()
        self._reader.protocol.bridge = self.__bridge
        self._reader.protocol.on_error = self.__on_error
        self._reader.connect()

        # Create write thread
        self.__send_thread         = threading.Thread(target=self.__write_thread)
        self.__send_thread.daemon  = True
        self.__send_thread.name    = 'Serial writing thread'
        self.__send_thread.start()

        self.__logger.info("Serial connection active on port {0}".format(self.__port))

    def stop(self):
        """
        Stops the serial communication if the serial connection is active.
        """

        if self.is_active():

            self.__logger.info("Stopping serial connection")

            self.__connected = False

            if not self.in_errror():
                self._reader.close()

            self.__send_event.set()
            self.__send_thread.join()

    def send(self, packet):
        """
        Queues a packet to be sent on the serial connection.

        :param packet: The packet that should be sent on the serial connection.
        """

        self.__send_buffer.append(packet)
        self.__send_event.set()