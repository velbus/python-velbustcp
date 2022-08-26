from serial import serial_for_url, PARITY_NONE, STOPBITS_ONE, EIGHTBITS
from velbustcp.lib.connection.serial.factory import find_port, set_serial_settings
from velbustcp.lib.settings.serial import SerialSettings


def test_find_port():
    options = SerialSettings()
    options.port = 12345
    port = find_port(options)

    #assert port == 12345


def test_settings():

    serial = serial_for_url("loop://", timeout=1)
    set_serial_settings(serial)

    assert serial.baudrate == 38400
    assert serial.parity == PARITY_NONE
    assert serial.stopbits == STOPBITS_ONE
    assert serial.bytesize == EIGHTBITS
    assert serial.xonxoff == 0
    assert not serial.timeout
    assert serial.dsrdtr == 1
    assert serial.rtscts == 0
