import argparse
import json
from threading import Event
import logging
import logging.handlers

from velbustcp.lib.connection.bridge import Bridge
from velbustcp.settings import settings_dict, set_default_settings, validate_and_set_settings


class Main():
    """Main class for the Velbus-TCP connection.

    Connects serial and TCP connection together.
    """

    def __init__(self):
        """Initialises the main class.
        """

        # Logger
        self.__logger = logging.getLogger(__name__)

        # Bridge
        self.__bridge = Bridge()
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


def setup_logging() -> logging.Logger:
    """Sets up logging for the library.

    Returns:
        logging.Logger: The set-up logger.
    """

    logger = logging.getLogger("velbustcp")

    if settings_dict["logging"]["type"] == "debug":
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    handler: logging.Handler = logging.StreamHandler()

    if settings_dict["logging"]["output"] == "syslog":
        handler = logging.handlers.SysLogHandler()

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger


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

    else:
        # Set default settings
        set_default_settings()

    # Setup logging
    logger = setup_logging()

    # Create main class
    main = Main()

    try:
        main.main_loop()

    except KeyboardInterrupt:
        logger.info("Interrupted, shutting down")

    except Exception as e:
        logger.exception(str(e))

    finally:
        main.stop()

    logger.info("Shutted down")
