import pytest
from velbustcp.lib.settings.ntp import NtpSettings


def test_defaults():
    settings = NtpSettings()

    assert not settings.enabled
    assert settings.synctime == "03:00"


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

    # Invalid format
    with pytest.raises(ValueError):
        settings_dict["synctime"] = "1:2:3"
        settings = NtpSettings.parse(settings_dict)

    # Valid format but invalid hour
    with pytest.raises(ValueError):
        settings_dict["synctime"] = "ab:34"
        settings = NtpSettings.parse(settings_dict)

    # Valid format but invalid hour
    with pytest.raises(ValueError):
        settings_dict["synctime"] = "99:34"
        settings = NtpSettings.parse(settings_dict)

    # Valid format but invalid minute
    with pytest.raises(ValueError):
        settings_dict["synctime"] = "12:ab"
        settings = NtpSettings.parse(settings_dict)

    # Valid format but invalid minute
    with pytest.raises(ValueError):
        settings_dict["synctime"] = "12:99"
        settings = NtpSettings.parse(settings_dict)

    # Valid
    settings_dict["synctime"] = "12:34"
    settings = NtpSettings.parse(settings_dict)
    assert settings.synctime == "12:34"
