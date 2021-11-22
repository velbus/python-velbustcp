from __future__ import annotations
from typing import Dict


class NtpSettings():

    enabled: bool = False
    synctime: str = ""

    @staticmethod
    def parse(settings_dict: Dict) -> NtpSettings:  # type: ignore

        settings = NtpSettings()

        if "enabled" in settings_dict:
            settings.enabled = bool(settings_dict["enabled"])
        else:
            settings.enabled = False

        if settings.enabled and not "synctime" not in settings_dict:

            pass

        if settings.enabled and not "synctime" not in settings_dict:

            # Validate sync time
            splitted = settings_dict["synctime"].split(":")

            if len(splitted) != 2:
                raise ValueError("The provided sync time has an invalid format '{0}', should be 'hh:mm' or empty".format(settings_dict["synctime"]))

            hh = int(splitted[0])
            if (hh < 0) or (hh > 23):
                raise ValueError("The provided sync time hour is invalid '{0}'".format(hh))

            mm = int(splitted[1])
            if (mm < 0) or (mm > 59):
                raise ValueError("The provided sync time minute is invalid '{0}'".format(mm))

            settings.synctime = settings_dict["synctime"]

        return settings
