import ipaddress
import os

settings_dict = dict()

def set_default_settings():
  
    settings_dict["connections"] = []
    default_conn = {}
    default_conn["host"] = ""
    default_conn["port"] = 27015
    default_conn["relay"] = True
    default_conn["ssl"] = False
    default_conn["pk"] = ""
    default_conn["cert"] = ""  
    default_conn["auth"] = False
    default_conn["authkey"] = ""    
    settings_dict["connections"].append(default_conn)

    settings_dict["serial"] = dict()
    settings_dict["serial"]["autodiscover"] = True
    settings_dict["serial"]["port"] = ""

    settings_dict["logging"] = dict()
    settings_dict["logging"]["type"] = "info"
    settings_dict["logging"]["output"] = "stream"

def validate_and_set_settings(settings):

    # Has connection(s)
    if "connections" in settings:

        settings_dict["connections"] = []

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

            settings_dict["connections"].append(conn_dict)

    # Serial
    if "serial" in settings:

        settings_dict["serial"] = dict()

        # Port
        if "port" in settings["serial"]:
            settings_dict["serial"]["port"] = settings["serial"]["port"]

        # Autodiscover
        if "autodiscover" in settings["serial"]:

            if (settings["serial"]["autodiscover"] != True) and (settings["serial"]["autodiscover"] != False):
                raise ValueError("Provided option autodiscover is invalid {0}".format(settings["serial"]["autodiscover"]))

            settings_dict["serial"]["autodiscover"] = settings["serial"]["autodiscover"]


    # Logging
    if "logging" in settings:

        settings_dict["logging"] = dict()
        
        if "type" in settings["logging"]:
            
            if (not settings["logging"]["type"] in ["debug", "info"]):
                raise ValueError("Provided option logging.type incorrect, expected 'debug' or 'info', got '{0}'".format(settings["logging"]["type"]))

            settings_dict["logging"]["type"] = settings["logging"]["type"]

        if "output" in settings["logging"]:
            
            if (not settings["logging"]["output"] in ["syslog", "stream"]):
                raise ValueError("Provided option logging.output incorrect, expected 'syslog' or 'stream', got '{0}'".format(settings["logging"]["output"]))

            settings_dict["logging"]["output"] = settings["logging"]["output"]    