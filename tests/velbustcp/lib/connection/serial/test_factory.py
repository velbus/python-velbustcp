from serial import serial_for_url, PARITY_NONE, STOPBITS_ONE, EIGHTBITS
from velbustcp.lib.connection.serial.factory import set_serial_settings


def test_settings():

    serial_for_url("loop://", timeout=1)
    serial_settings = set_serial_settings()

    assert serial_settings.get("baudrate") == 38400
    assert serial_settings.get("parity") == PARITY_NONE
    assert serial_settings.get("stopbits") == STOPBITS_ONE
    assert serial_settings.get("bytesize") == EIGHTBITS
    assert serial_settings.get("xonxoff") == 0
    assert not serial_settings.get("timeout")
    assert serial_settings.get("dsrdtr") == 1
    assert serial_settings.get("rtscts") == 0
