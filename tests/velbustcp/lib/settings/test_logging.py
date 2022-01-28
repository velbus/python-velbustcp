import pytest

from velbustcp.lib.settings.logging import LoggingSettings, LOGGING_TYPES, LOGGING_OUTPUT


def test_defaults():
    settings = LoggingSettings()

    assert settings.type == "info"
    assert settings.output == "stream"


def test_parse():

    settings_dict = dict()

    for logging_type in LOGGING_TYPES:
        for logging_output in LOGGING_OUTPUT:
            settings_dict["type"] = logging_type
            settings_dict["output"] = logging_output
            settings = LoggingSettings.parse(settings_dict)

            assert settings.output == logging_output
            assert settings.type == logging_type


def test_invalid_type():
    settings = dict()
    settings["type"] = "unknown"

    with pytest.raises(ValueError):
        LoggingSettings.parse(settings)


def test_invalid_output():
    settings = dict()
    settings["output"] = "unknown"

    with pytest.raises(ValueError):
        LoggingSettings.parse(settings)
