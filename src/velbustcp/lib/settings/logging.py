from __future__ import annotations
from typing import Dict


class LoggingSettings():

    type: str = "info"
    output: str = "stream"

    @staticmethod
    def parse(settings_dict: Dict) -> LoggingSettings:  # type: ignore
        settings = LoggingSettings()

        if "type" in settings_dict:

            if (not settings_dict["type"] in ["debug", "info"]):
                raise ValueError("Provided option logging.type incorrect, expected 'debug' or 'info', got '{0}'".format(settings_dict["type"]))

            settings.type = settings_dict["type"]

        if "output" in settings_dict:

            if (not settings_dict["output"] in ["syslog", "stream"]):
                raise ValueError("Provided option logging.output incorrect, expected 'syslog' or 'stream', got '{0}'".format(settings_dict["output"]))

            settings.output = settings_dict["output"]

        return settings
