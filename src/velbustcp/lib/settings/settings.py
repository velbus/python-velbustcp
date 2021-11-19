from typing import List

from velbustcp.lib.settings.serial import SerialSettings
from velbustcp.lib.settings.network import NetworkSettings
from velbustcp.lib.settings.ntp import NtpSettings
from velbustcp.lib.settings.logging import LoggingSettings

network_settings: List[NetworkSettings] = [NetworkSettings()]
serial_settings: SerialSettings = SerialSettings()
ntp_settings: NtpSettings = NtpSettings()
logging_settings: LoggingSettings = LoggingSettings()

def validate_and_set_settings(settings):

    # NTP configuration
    if "ntp" in settings:
        ntp_settings = NtpSettings.parse(settings["ntp"])
    
    # Has connection(s)
    if "connections" in settings:
        network_settings = [] # clear default

        for connection in settings["connections"]:
            network_settings.append(NetworkSettings.parse(connection))

    # Serial
    if "serial" in settings:
        serial_settings = SerialSettings.parse(settings)

    # Logging
    if "logging" in settings:
        logging_settings = LoggingSettings.parse(settings)