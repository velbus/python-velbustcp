import serial_asyncio_fast
from velbustcp.lib.settings.serial import SerialSettings
from velbustcp.lib.util.util import search_for_serial


def set_serial_settings() -> dict:
    """Returns settings for a Serial object for use with the Velbus protocol."""
    return {
        'baudrate': 38400,
        'parity': serial_asyncio_fast.serial.PARITY_NONE,
        'stopbits': serial_asyncio_fast.serial.STOPBITS_ONE,
        'bytesize': serial_asyncio_fast.serial.EIGHTBITS,
        'xonxoff': 0,
        'timeout': None,
        'dsrdtr': 1,
        'rtscts': 0
    }


def find_port(options: SerialSettings) -> str:
    """Finds a port for the serial object."""
    if options.autodiscover:
        ports = search_for_serial()
        return next((port for port in ports), options.port)
    return options.port