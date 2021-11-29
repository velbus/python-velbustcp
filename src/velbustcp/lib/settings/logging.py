from typing import Dict

LOGGING_TYPES = ["debug", "info"]
LOGGING_OUTPUT = ["syslog", "stream"]


class LoggingSettings():

    type: str = "info"
    output: str = "stream"

    @staticmethod
    def parse(settings_dict):
        # type: (Dict[str, str]) -> LoggingSettings

        settings = LoggingSettings()

        if "type" in settings_dict:

            if (not settings_dict["type"] in LOGGING_TYPES):
                raise ValueError("Provided option logging.type incorrect, expected 'debug' or 'info', got '{0}'".format(settings_dict["type"]))

            settings.type = settings_dict["type"]

        if "output" in settings_dict:

            if (not settings_dict["output"] in LOGGING_OUTPUT):
                raise ValueError("Provided option logging.output incorrect, expected 'syslog' or 'stream', got '{0}'".format(settings_dict["output"]))

            settings.output = settings_dict["output"]

        return settings
