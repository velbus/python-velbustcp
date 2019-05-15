import argparse
import json
from threading import Event
import logging
import logging.handlers

from lib.connection.bridge import Bridge

class Main():
    """
    Main class for the Velbus-TCP connection.

    Connects serial and TCP connection together.
    """

    def __init__(self, settings):
        """
        Initialises the main class.
        """

        # Logger
        self.__logger = logging.getLogger("VelbusTCP")

        # Bridge
        self.__bridge = Bridge(settings)    
        self.__bridge.start()    
   

    def main_loop(self):
        """
        Main loop for the program, blocks infinitely until it receives a KeyboardInterrupt.
        """

        q = Event()
        q.wait()

    def stop(self):
        """
        Stops bridge.
        """

        self.__bridge.stop()

def setup_logging(options):
    
    logger = logging.getLogger("VelbusTCP")
    if "type" in options and options["type"] == "debug":
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    handler = None

    if "output" in options and options["output"] == "syslog":
        handler = logging.handlers.SysLogHandler()
    else:
        handler = logging.StreamHandler()

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger        

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Velbus communication")
    parser.add_argument("--settings", help="Settings file", required=False, default="settings.json")
    args = parser.parse_args()

    # Open settings file
    with open(args.settings, 'r') as f:
        settings = json.load(f)

    # Setup logging
    logger = setup_logging(options=settings["logging"])   

    # Create main class
    main = Main(settings)

    try:
        main.main_loop()

    except KeyboardInterrupt:
        logger.info("Interrupted, shutting down")

    except Exception as e:
        logger.exception(str(e))

    finally:
        main.stop()

    logger.info("Shutted down")