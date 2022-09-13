import pytest
import tempfile
from velbustcp.lib.settings.network import NetworkSettings


def test_defaults():
    settings = NetworkSettings()

    assert settings.relay
    assert settings.host == "0.0.0.0"
    assert settings.port == 27015
    assert not settings.ssl
    assert settings.pk == ""
    assert settings.cert == ""
    assert not settings.auth
    assert settings.auth_key == ""
    assert settings.address == ("0.0.0.0", 27015)


def test_parse_host():

    settings_dict = dict()

    # Valid host
    settings_dict["host"] = "127.0.0.1"
    settings = NetworkSettings.parse(settings_dict)
    assert settings.host == "127.0.0.1"

    # Invalid host
    settings_dict["host"] = "invalid_host"

    with pytest.raises(ValueError):
        NetworkSettings.parse(settings_dict)


def test_parse_port():

    settings_dict = dict()

    # Valid host
    settings_dict["port"] = "12345"
    settings = NetworkSettings.parse(settings_dict)
    assert settings.port == 12345

    # Invalid port
    settings_dict["port"] = "invalid_port"

    with pytest.raises(ValueError):
        NetworkSettings.parse(settings_dict)

    # Invalid port range
    settings_dict["port"] = "99999"

    with pytest.raises(ValueError):
        NetworkSettings.parse(settings_dict)


def test_parse_relay():

    settings_dict = dict()

    # Valid relay
    settings_dict["relay"] = "false"
    settings = NetworkSettings.parse(settings_dict)
    assert not settings.relay

    # Invalid relay
    settings_dict["relay"] = "invalid_relay"
    assert not settings.relay


def test_parse_ssl():

    settings_dict = dict()

    # Test SSL enabled, but no PK given
    settings_dict["ssl"] = "true"

    with pytest.raises(ValueError):
        settings_dict["pk"] = ""
        NetworkSettings.parse(settings_dict)

    with tempfile.NamedTemporaryFile(delete=True) as temp:

        settings_dict["pk"] = temp.name

        # Test SSL enabled, but no cert specified
        with pytest.raises(ValueError):
            settings_dict["cert"] = ""
            NetworkSettings.parse(settings_dict)

        # Valid everything
        settings_dict["cert"] = temp.name
        settings = NetworkSettings.parse(settings_dict)

        assert settings.ssl
        assert settings.pk == temp.name
        assert settings.cert == temp.name


def test_parse_auth():

    settings_dict = dict()

    # Default auth
    settings = NetworkSettings.parse(settings_dict)
    assert not settings.auth

    # Test SSL enabled, but no auth_key given
    settings_dict["auth"] = "true"

    with pytest.raises(ValueError):
        settings_dict["auth_key"] = ""
        NetworkSettings.parse(settings_dict)

    # Valid everything
    settings_dict["auth_key"] = "12345"
    settings = NetworkSettings.parse(settings_dict)

    assert settings.auth
    assert settings.auth_key == "12345"
