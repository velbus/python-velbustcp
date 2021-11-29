import ipaddress
import os
from typing import Dict, Tuple
from velbustcp.lib.util.util import str2bool


class NetworkSettings():

    relay: bool = True
    host: str = "0.0.0.0"
    port: int = 27015
    ssl: bool = False
    pk: str = ""
    cert: str = ""
    auth: bool = False
    auth_key: str = ""

    @property
    def address(self) -> Tuple[str, int]:
        return (self.host, self.port)

    @staticmethod
    def parse(settings_dict):
        # type: (Dict[str, str]) -> NetworkSettings

        settings = NetworkSettings()

        # Host
        if "host" in settings_dict:
            settings.host = settings_dict["host"]

            # Make sure host is valid
            ipaddress.ip_address(settings.host)

        # Port
        if "port" in settings_dict:
            settings.port = int(settings_dict["port"])

            if (settings.port < 0) or (settings.port > 65535):
                raise ValueError("The provided port is invalid {0}".format(settings.port))

        # Relay
        if "relay" in settings_dict:
            settings.relay = str2bool(settings_dict["relay"])

        # SSL
        if "ssl" in settings_dict:
            ssl_enabled = str2bool(settings_dict["ssl"])

            if ssl_enabled:

                # PK
                if ("pk" not in settings_dict) or (settings_dict["pk"] == "") or (not os.path.isfile(settings_dict["pk"])):
                    raise ValueError("Provided private key not found or non given while SSL is enabled")

                # Certificate
                if ("cert" not in settings_dict) or (settings_dict["cert"] == "") or (not os.path.isfile(settings_dict["cert"])):
                    raise ValueError("Provided certificate not found or non given while SSL is enabled")

                settings.pk = settings_dict["pk"]
                settings.cert = settings_dict["cert"]

            settings.ssl = ssl_enabled

        # Auth
        if "auth" in settings_dict:
            settings.auth = bool(settings_dict["auth"])

            if settings.auth:

                if not ("auth_key" in settings_dict) or (settings_dict["auth_key"] == ""):
                    raise ValueError("No auth key provided or is empty")

                settings.auth_key = settings_dict["auth_key"]

        return settings
