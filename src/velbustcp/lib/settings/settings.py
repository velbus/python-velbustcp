from typing import List

from velbustcp.lib.settings.serial import SerialSettings
from velbustcp.lib.settings.network import NetworkSettings
from velbustcp.lib.settings.logging import LoggingSettings

network_settings: List[NetworkSettings] = [NetworkSettings()]
serial_settings: SerialSettings = SerialSettings()
logging_settings: LoggingSettings = LoggingSettings()


def validate_and_set_settings(settings):

    # Has connection(s)
    if "connections" in settings:
        global network_settings
        network_settings = []  # clear default

        for connection in settings["connections"]:
            network_settings.append(NetworkSettings.parse(connection))

    # Serial
    if "serial" in settings:
        global serial_settings
        serial_settings = SerialSettings.parse(settings["serial"])

    # Logging
    if "logging" in settings:
        global logging_settings
        logging_settings = LoggingSettings.parse(settings["logging"])
