from pytest_mock import MockFixture
from velbustcp.lib.connection.serial.bus import Bus
from velbustcp.lib.settings.serial import SerialSettings


def test_defaults(mocker: MockFixture):

    # Arrange
    options = SerialSettings()
    bus = Bus(options=options)

    # Assert
    assert not bus.is_active()
