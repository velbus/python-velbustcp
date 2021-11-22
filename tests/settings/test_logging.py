from velbustcp.lib.settings.logging import LoggingSettings, LOGGING_TYPES, LOGGING_OUTPUT


def test_defaults():
    settings = LoggingSettings()

    assert settings.type == "info"
    assert settings.output == "stream"


def test_parse():

    settings = dict()

    for logging_type in LOGGING_TYPES:
        for logging_output in LOGGING_OUTPUT:
            settings["type"] = logging_type
            settings["output"] = logging_output
            LoggingSettings.parse(settings)
