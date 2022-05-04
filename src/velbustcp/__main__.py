import argparse
import json
from threading import Event

from velbustcp.lib.connection.bridge import Bridge
from velbustcp.lib.connection.serial.bus import Bus
from velbustcp.lib.connection.tcp.networkmanager import NetworkManager
from velbustcp.lib.ntp.ntp import Ntp
from velbustcp.lib.settings.settings import serial_settings, network_settings, ntp_settings, logging_settings, validate_and_set_settings
from velbustcp.lib.util.util import setup_logging


class Main():
    """Main class for the Velbus-TCP connection.

    Connects serial and TCP connection together.
    """

    def __init__(self):
        """Initialises the main class.
        """

        # Bridge
        bus = Bus(options=serial_settings)
        network_manager = NetworkManager(connections=network_settings)
        ntp = Ntp(options=ntp_settings)

        self.__bridge = Bridge(bus, network_manager, ntp)
        self.__bridge.start()

    def main_loop(self):
        """Main loop for the program, blocks infinitely until it receives a KeyboardInterrupt.
        """

        q = Event()
        q.wait()

    def stop(self):
        """Stops bridge.
        """

        self.__bridge.stop()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Velbus communication")
    parser.add_argument("--settings", help="Settings file", required=False)
    args = parser.parse_args()

    # If settings are supplied, read and validate them
    if args.settings:

        # Open settings file
        with open(args.settings, 'r') as f:
            settings = json.load(f)

        validate_and_set_settings(settings)

    # Setup logging
    logger = setup_logging(logging_settings)

    # Create main class
    main = Main()

    try:
        main.main_loop()

    except KeyboardInterrupt:
        logger.info("Interrupted, shutting down")

    except Exception as e:
        logger.exception(e)

    finally:
        main.stop()

    logger.info("Shutted down")
