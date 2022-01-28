import serial

from velbustcp.lib.settings.serial import SerialSettings
from velbustcp.lib.util.util import search_for_serial


def set_serial_settings(s: serial.Serial):
    """Sets settings on a Serial object for use with the Velbus protcol

    Args:
        s (serial.Serial): A serial object.
    """

    s.baudrate = 38400
    s.parity = serial.PARITY_NONE
    s.stopbits = serial.STOPBITS_ONE
    s.bytesize = serial.EIGHTBITS
    s.xonxoff = 0
    s.timeout = None
    s.dsrdtr = 1
    s.rtscts = 0


def construct_serial_obj(port: str) -> serial.Serial:
    """Constructs a serial object for use with the Velbus protocol.

    Args:
        port (str): A port suitable for the serial object.

    Returns:
        serial.Serial: A serial object.
    """

    s = serial.Serial(port)
    set_serial_settings(s)

    return s


def find_port(options: SerialSettings) -> str:
    """[summary]

    Args:
        options (SerialSettings): [description]

    Returns:
        str: A port name
    """

    # If we need to autodiscover port
    if options.autodiscover:
        ports = search_for_serial()

        return next((port for port in ports), options.port)

    # No port found (or no autodiscover)
    return options.port
