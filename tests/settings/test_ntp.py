import pytest
import tempfile
from velbustcp.lib.settings.network import NetworkSettings

from velbustcp.lib.settings.ntp import NtpSettings


def test_defaults():
    settings = NtpSettings()

    assert not settings.enabled
    assert not settings.synctime


def test_parse_enabled():

    settings_dict = dict()

    # Default
    settings = NtpSettings.parse(settings_dict)
    assert not settings.enabled

    # Valid
    settings_dict["enabled"] = "true"
    settings = NtpSettings.parse(settings_dict)
    assert settings.enabled

def test_parse_synctime():

    settings_dict = dict()

    # Default
    settings = NtpSettings.parse(settings_dict)
    assert not settings.synctime

    # Invalid format
    with pytest.raises(ValueError):
        settings_dict["synctime"] = "1:2:3"
        settings = NtpSettings.parse(settings_dict)

    # Valid format but invalid hour
    with pytest.raises(ValueError):
        settings_dict["synctime"] = "ab:34"
        settings = NtpSettings.parse(settings_dict)

    # Valid format but invalid minute
    with pytest.raises(ValueError):
        settings_dict["synctime"] = "12:ab"
        settings = NtpSettings.parse(settings_dict)


















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

