import logging
from typing import List
import serial
from velbustcp.lib.settings.logging import LoggingSettings
from velbustcp.lib.consts import PRODUCT_IDS



def str2bool(v: str) -> bool:
    return str(v).lower() in ["true", "yes", "y", "t", "1"]

def setup_logging(settings: LoggingSettings) -> logging.Logger:
    """Sets up logging for the library.

    Returns:
        logging.Logger: The set-up logger.
    """

    print(__name__)
    logger = logging.getLogger("velbustcp")

    if settings.type == "debug":
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    handler: logging.Handler = logging.StreamHandler()

    if settings.output == "syslog":
        handler = logging.handlers.SysLogHandler()

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(message)s')
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