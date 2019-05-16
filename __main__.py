import argparse
import json
from threading import Event
import logging
import logging.handlers
import os

from lib.connection.bridge import Bridge
import lib.settings

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

def setup_logging():
    
    logger = logging.getLogger("VelbusTCP")

    if lib.settings.settings["logging"]["type"] == "debug":
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    handler = None

    if lib.settings.settings["logging"]["output"] == "syslog":
        handler = logging.handlers.SysLogHandler()
    else:
        handler = logging.StreamHandler()

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(module)s - %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger    

def set_default_settings():
    
    lib.settings.settings["tcp"] = dict()
    lib.settings.settings["tcp"]["port"] = 27015
    lib.settings.settings["tcp"]["relay"] = True
    lib.settings.settings["tcp"]["ssl"] = False
    lib.settings.settings["tcp"]["pk"] = ""
    lib.settings.settings["tcp"]["cert"] = ""
    lib.settings.settings["tcp"]["auth"] = False
    lib.settings.settings["tcp"]["authkey"] = ""    

    lib.settings.settings["serial"] = dict()
    lib.settings.settings["serial"]["autodiscover"] = True
    lib.settings.settings["serial"]["port"] = ""

    lib.settings.settings["logging"] = dict()
    lib.settings.settings["logging"]["type"] = "info"
    lib.settings.settings["logging"]["output"] = "stream"

def validate_settings(settings):

    # TCP
    if "tcp" in settings:
        
        # Port
        if "port" in settings["tcp"]:
           
            lib.settings.settings["tcp"]["port"] = int(settings["tcp"]["port"])
            if (lib.settings.settings["tcp"]["port"] < 0) or (lib.settings.settings["tcp"]["port"] > 65535):
                raise ValueError("The provided port is invalid {0}".format(lib.settings.settings["tcp"]["port"]))

        # SSL
        if "ssl" in settings["tcp"]:

            # SSL enabled/disabled
            if (settings["tcp"]["ssl"] != True) and (settings["tcp"]["ssl"] != False):
                raise ValueError("Provided option ssl is invalid {0}".format(settings["tcp"]["ssl"]))

            if settings["tcp"]["ssl"]:

                # PK
                if (not "pk" in settings["tcp"]) or (settings["tcp"]["pk"] == "") or (not os.path.isfile(settings["tcp"]["pk"])):
                    raise ValueError("Provided private key not found or non given while SSL is enabled")

                # Certificate
                if (not "cert" in settings["tcp"]) or (settings["tcp"]["cert"] == "") or (not os.path.isfile(settings["tcp"]["cert"])):
                    raise ValueError("Provided certificate not found or non given while SSL is enabled")

                lib.settings.settings["tcp"]["pk"] = settings["tcp"]["pk"] 
                lib.settings.settings["tcp"]["cert"] = settings["tcp"]["cert"]                    

            lib.settings.settings["tcp"]["ssl"] = settings["tcp"]["ssl"]       
        

        # Auth
        if "auth" in settings["tcp"]:

            # Auth enabled/disabled
            if (settings["tcp"]["auth"] != True) and (settings["tcp"]["auth"] != False):
                raise ValueError("Provided option auth is invalid {0}".format(settings["tcp"]["auth"]))

            lib.settings.settings["tcp"]["auth"] = settings["tcp"]["auth"]      

            if settings["tcp"]["auth"]:

                if not ("auth_key" in settings["tcp"]) or (settings["tcp"]["auth_key"] == ""):
                    raise ValueError("No auth key provided or is empty")

                lib.settings.settings["tcp"]["authkey"] = settings["tcp"]["auth_key"]                        

    # Serial
    if "serial" in settings:

        # Port
        if "port" in settings["serial"]:
            lib.settings.settings["serial"]["port"] = settings["serial"]["port"]

        # Autodiscover
        if ("autodiscover" in settings["serial"]):

            if (settings["serial"]["autodiscover"] != True) and (settings["serial"]["autodiscover"] != False):
                raise ValueError("Provided option autodiscover is invalid {0}".format(settings["serial"]["autodiscover"]))

            lib.settings.settings["serial"]["autodiscover"] = settings["serial"]["autodiscover"]


    # Logging
    if "logging" in settings:
        
        if ("type" in settings["logging"]):
            
            if (not settings["logging"]["type"] in ["debug", "info"]):
                raise ValueError("Provided option logging.type incorrect, expected 'debug' or 'info', got '{0}'".format(settings["logging"]["type"]))

            lib.settings.settings["logging"]["type"] = settings["logging"]["type"]

        if ("output" in settings["logging"]):
            
            if (not settings["logging"]["output"] in ["syslog", "stream"]):
                raise ValueError("Provided option logging.output incorrect, expected 'syslog' or 'stream', got '{0}'".format(settings["logging"]["output"]))

            lib.settings.settings["logging"]["output"] = settings["logging"]["output"]            
         
if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="Velbus communication")
    parser.add_argument("--settings", help="Settings file", required=False, default="settings.json")
    args = parser.parse_args()

    # Set default settings
    set_default_settings()

    # If settings are supplied, read and validate them
    if args.settings:

        # Open settings file
        with open(args.settings, 'r') as f:
            settings = json.load(f)

        validate_settings(settings)

    # Setup logging
    logger = setup_logging()   

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