from velbustcp.lib.settings.settings import SerialSettings


def test_defaults():

    settings = SerialSettings()
    assert settings.autodiscover
    assert not settings.port


def test_parse_port():

    settings_dict = dict()
    settings_dict["port"] = "/dev/ttyAMA0"
    settings = SerialSettings.parse(settings_dict)
    assert settings.port == "/dev/ttyAMA0"


def test_parse_autodiscover():

    settings_dict = dict()
    settings_dict["autodiscover"] = "true"
    settings = SerialSettings.parse(settings_dict)
    assert settings.autodiscover
