import serial


def construct_serial_obj(port):

    return serial.Serial(
        port=port,
        baudrate=38400,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS,
        xonxoff=0,
        timeout=None,
        dsrdtr=1,
        rtscts=0,
    )
