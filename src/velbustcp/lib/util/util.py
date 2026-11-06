import logging
import logging.handlers
import os
import socket
from typing import List
import serial
import serial.tools.list_ports
from velbustcp.lib.settings.logging import LoggingSettings
from velbustcp.lib.consts import PRODUCT_IDS


SYSLOG_SOCKETS = ["/dev/log", "/var/run/syslog"]


def str2bool(v: str) -> bool:
    return str(v).lower() in ["true", "yes", "y", "t", "1"]


def setup_logging(settings: LoggingSettings) -> logging.Logger:
    """Sets up logging for the library.

    Returns:
        logging.Logger: The set-up logger.
    """

    logger = logging.getLogger(settings.name)

    # Set type
    if settings.type == "debug":
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Set handler
    handler: logging.Handler
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(message)s')
    if settings.output == "syslog":
        handler = logging.handlers.SysLogHandler()
    elif settings.output == "syslog-local":
        if not hasattr(socket, "AF_UNIX"):
            raise ValueError("Logging output 'syslog-local' is not supported on this platform")

        address = next((path for path in SYSLOG_SOCKETS if os.path.exists(path)), SYSLOG_SOCKETS[0])
        handler = logging.handlers.SysLogHandler(address=address)
        handler.ident = "velbustcp: "
        handler.append_nul = False
        # The local syslog adds its own timestamp
        formatter = logging.Formatter('%(levelname)s - %(module)s - %(message)s')
    else:
        handler = logging.StreamHandler()

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


def search_for_serial() -> List[str]:
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
