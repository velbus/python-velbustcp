from __future__ import annotations
from typing import Dict


class SerialSettings():

    port: str = ""
    autodiscover: bool = True

    @staticmethod
    def parse(settings_dict: Dict) -> SerialSettings:   # type: ignore
        settings = SerialSettings()

        # Port
        if "port" in settings_dict:
            settings.port = settings_dict["port"]

        # Autodiscover
        if "autodiscover" in settings_dict:
            settings.autodiscover = bool(settings_dict["autodiscover"])

        return settings
