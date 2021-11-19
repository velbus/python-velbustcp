import pytest

from velbustcp.lib.packet.packetbuffer import PacketBuffer
from velbustcp.lib.consts import STX

realign_data = [
    (bytearray([0x01, 0x04, not STX, 0x09, 0x04]), 0),  # No STX present
    (bytearray([STX, 0x04, 0x47, 0x09, 0x04]), 0),      # STX at start, so should skip it
    (bytearray([0x01, 0x04, STX, 0x09, 0x04]), 3)       # STX present
]


@pytest.mark.parametrize("data, expected_result", realign_data)
def test_realign(data, expected_result):
    parser = PacketBuffer()
    parser.feed(data)
    parser.realign()
    assert len(parser.buffer) == expected_result


indexing_data = [
    (0, 0x01),                             # Single item indexing [0]
    (slice(0, 2), bytearray([0x01, 0x02]))  # Indexing by slicing [0:2]
]


@pytest.mark.parametrize("data, expected_result", indexing_data)
def test_index(data, expected_result):
    buffer = PacketBuffer()
    buffer.feed(bytearray([0x01, 0x02]))
    assert expected_result == buffer[data]
