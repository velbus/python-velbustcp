import ipaddress
import os
from typing import Any, Dict

settings_dict: Dict[str, Any] = dict()


def set_default_settings():

    settings_dict["ntp"] = dict()
    settings_dict["ntp"]["enabled"] = False
    settings_dict["ntp"]["synctime"] = ""

    settings_dict["connections"] = []
    default_conn = {}
    default_conn["host"] = ""
    default_conn["port"] = 27015    # type: ignore
    default_conn["relay"] = True    # type: ignore
    default_conn["ssl"] = False     # type: ignore
    default_conn["pk"] = ""
    default_conn["cert"] = ""
    default_conn["auth"] = False    # type: ignore
    default_conn["authkey"] = ""
    settings_dict["connections"].append(default_conn)

    settings_dict["serial"] = dict()
    settings_dict["serial"]["autodiscover"] = True
    settings_dict["serial"]["port"] = ""

    settings_dict["logging"] = dict()
    settings_dict["logging"]["type"] = "info"
    settings_dict["logging"]["output"] = "stream"


def validate_and_set_settings(settings):

    # NTP configuration
    if "ntp" in settings:

        settings_dict["ntp"] = {}

        if "enabled" in settings["ntp"]:
            settings_dict["ntp"]["enabled"] = bool(settings["ntp"]["enabled"])
        else:
            settings_dict["ntp"]["enabled"] = False

        if "synctime" in settings["ntp"] and settings["ntp"]["synctime"] != "":

            # Validate sync time
            splitted = settings["ntp"]["synctime"].split(":")

            if len(splitted) != 2:
                raise ValueError("The provided sync time has an invalid format '{0}', should be 'hh:mm' or empty".format(settings["ntp"]["synctime"]))

            hh = int(splitted[0])
            if (hh < 0) or (hh > 23):
                raise ValueError("The provided sync time hour is invalid '{0}'".format(hh))

            mm = int(splitted[1])
            if (mm < 0) or (mm > 59):
                raise ValueError("The provided sync time minute is invalid '{0}'".format(mm))

            settings_dict["ntp"]["synctime"] = settings["ntp"]["synctime"]

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
                conn_dict["relay"] = bool(connection["relay"])
            else:
                conn_dict["relay"] = False

            # SSL
            if "ssl" in connection:

                if bool(connection["ssl"]):

                    # PK
                    if ("pk" not in connection) or (connection["pk"] == "") or (not os.path.isfile(connection["pk"])):
                        raise ValueError("Provided private key not found or non given while SSL is enabled")

                    # Certificate
                    if ("cert" not in connection) or (connection["cert"] == "") or (not os.path.isfile(connection["cert"])):
                        raise ValueError("Provided certificate not found or non given while SSL is enabled")

                    conn_dict["pk"] = connection["pk"]
                    conn_dict["cert"] = connection["cert"]

                conn_dict["ssl"] = bool(connection["ssl"])

            # Auth
            if "auth" in connection:
                conn_dict["auth"] = bool(connection["auth"])

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
            settings_dict["serial"]["autodiscover"] = bool(settings["serial"]["autodiscover"])

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
