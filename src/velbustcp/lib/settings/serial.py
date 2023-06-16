from typing import Dict  # noqa: F401
from velbustcp.lib.util.util import str2bool


class SerialSettings():

    port: str = ""
    autodiscover: bool = True

    @staticmethod
    def parse(settings_dict):
        # type: (Dict[str, str]) -> SerialSettings

        settings = SerialSettings()

        # Port
        if "port" in settings_dict:
            settings.port = settings_dict["port"]

        # Autodiscover
        if "autodiscover" in settings_dict:
            settings.autodiscover = str2bool(settings_dict["autodiscover"])

        return settings
