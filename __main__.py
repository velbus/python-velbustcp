import argparse
import json
from threading import Event
import logging
import logging.handlers
import os
import ipaddress

from lib.connection.bridge import Bridge
import lib.settings

class Main():
    """
    Main class for the Velbus-TCP connection.

    Connects serial and TCP connection together.
    """

    def __init__(self):
        """
        Initialises the main class.
        """

        # Logger
        self.__logger = logging.getLogger("VelbusTCP")

        # Bridge
        self.__bridge = Bridge()    
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
    
    lib.settings.settings["connections"] = []

    default_conn = {}
    default_conn["host"] = ""
    default_conn["port"] = 27015
    default_conn["relay"] = True
    
    default_conn["ssl"] = False
    default_conn["pk"] = ""
    default_conn["cert"] = ""
    
    default_conn["auth"] = False
    default_conn["authkey"] = ""    
    lib.settings.settings["connections"].append(default_conn)

    lib.settings.settings["serial"] = dict()
    lib.settings.settings["serial"]["autodiscover"] = True
    lib.settings.settings["serial"]["port"] = ""

    lib.settings.settings["logging"] = dict()
    lib.settings.settings["logging"]["type"] = "info"
    lib.settings.settings["logging"]["output"] = "stream"

def validate_settings(settings):

    # Has connection(s)
    if "connections" in settings:

        lib.settings.settings["connections"] = []

        for connection in settings["connections"]:

            conn_dict = {}  

            # Host
            if "host" in connection:
                conn_dict["host"] = connection["host"]

                # Make sure host is empty (all), or a valid IPv4/IPv6
                if conn_dict["host"] != "":
                    ipaddress.ip_address(conn_dict["host"])

            # Port
            if "port" in connection:
            
                conn_dict["port"] = int(connection["port"])
                if (conn_dict["port"] < 0) or (conn_dict["port"] > 65535):
                    raise ValueError("The provided port is invalid {0}".format(conn_dict["port"]))

            # SSL
            if "relay" in connection:

                # Relay enabled/disabled
                if (connection["relay"] != True) and (connection["relay"] != False):
                    raise ValueError("Provided option for relay is invalid {0}".format(connection["relay"]))                    
            
                conn_dict["relay"] = connection["relay"]                 

            # SSL
            if "ssl" in connection:

                # SSL enabled/disabled
                if (connection["ssl"] != True) and (connection["ssl"] != False):
                    raise ValueError("Provided option ssl is invalid {0}".format(connection["ssl"]))

                if connection["ssl"]:

                    # PK
                    if (not "pk" in connection) or (connection["pk"] == "") or (not os.path.isfile(connection["pk"])):
                        raise ValueError("Provided private key not found or non given while SSL is enabled")

                    # Certificate
                    if (not "cert" in connection) or (connection["cert"] == "") or (not os.path.isfile(connection["cert"])):
                        raise ValueError("Provided certificate not found or non given while SSL is enabled")

                    conn_dict["pk"] = connection["pk"] 
                    conn_dict["cert"] = connection["cert"]                    

                conn_dict["ssl"] = connection["ssl"]       
            
            # Auth
            if "auth" in connection:

                # Auth enabled/disabled
                if (connection["auth"] != True) and (connection["auth"] != False):
                    raise ValueError("Provided option auth is invalid {0}".format(connection["auth"]))

                conn_dict["auth"] = connection["auth"]      

                if connection["auth"]:

                    if not ("auth_key" in connection) or (connection["auth_key"] == ""):
                        raise ValueError("No auth key provided or is empty")

                    conn_dict["authkey"] = connection["auth_key"]                        

            lib.settings.settings["connections"].append(conn_dict)

    # Serial
    if "serial" in settings:

        lib.settings.settings["serial"] = dict()

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

        lib.settings.settings["logging"] = dict()
        
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
    parser.add_argument("--settings", help="Settings file", required=False)
    args = parser.parse_args()   

    # If settings are supplied, read and validate them
    if args.settings:

        # Open settings file
        with open(args.settings, 'r') as f:
            settings = json.load(f)

        validate_settings(settings)
    
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