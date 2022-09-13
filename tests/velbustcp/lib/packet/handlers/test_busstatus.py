from velbustcp.lib.consts import ETX, STX, PRIORITY_HIGH, COMMAND_BUS_OFF, COMMAND_BUS_ACTIVE, COMMAND_BUS_BUFFERFULL, COMMAND_BUS_BUFFERREADY
from velbustcp.lib.packet.handlers.busstatus import BusStatus

BUS_ACTIVE_DATA = bytearray([ETX, PRIORITY_HIGH, 0x00, 0x01, COMMAND_BUS_ACTIVE, 0x00, STX])
BUS_OFF_DATA = bytearray([ETX, PRIORITY_HIGH, 0x00, 0x01, COMMAND_BUS_OFF, 0x00, STX])
BUS_BUFFER_READY_DATA = bytearray([ETX, PRIORITY_HIGH, 0x00, 0x01, COMMAND_BUS_BUFFERREADY, 0x00, STX])
BUS_BUFFER_FULL_DATA = bytearray([ETX, PRIORITY_HIGH, 0x00, 0x01, COMMAND_BUS_BUFFERFULL, 0x00, STX])


def test_default():
    status = BusStatus()

    assert status.buffer_ready
    assert status.active
    assert status.alive


def test_alive():
    status = BusStatus()

    status.receive_packet(BUS_ACTIVE_DATA)
    status.receive_packet(BUS_BUFFER_READY_DATA)
    assert status.alive
    assert status.active
    assert status.buffer_ready

    status.receive_packet(BUS_BUFFER_FULL_DATA)
    assert not status.alive
    assert not status.buffer_ready
    assert status.active

    status.receive_packet(BUS_OFF_DATA)
    assert not status.alive
    assert not status.buffer_ready
    assert not status.active

    status.receive_packet(BUS_BUFFER_READY_DATA)
    assert not status.alive
    assert status.buffer_ready
    assert not status.active

    status.receive_packet(BUS_ACTIVE_DATA)
    assert status.alive
    assert status.buffer_ready
    assert status.active
