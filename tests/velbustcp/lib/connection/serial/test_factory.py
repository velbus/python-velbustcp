from velbustcp.lib.connection.serial.factory import construct_serial_obj

def test_factory():

    serial = construct_serial_obj("COM0")
    assert serial.port == "COM0"
