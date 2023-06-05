import pytest


from velbustcp.lib.packet.utils import calculate_data_length_from_flag


TEST_LENGTH_DICT = [
    (0x00, 0),
    (0x01, 1),
    (0x02, 2),
    (0x03, 3),
    (0x04, 4),
    (0x05, 5),
    (0x06, 6),
    (0x07, 7),
    (0x08, 8),
    (0x09, 12),
    (0x0A, 16),
    (0x0B, 20),
    (0x0C, 24),
    (0x0D, 32),
    (0x0E, 48),
    (0x0F, 64)
]


@pytest.mark.parametrize("flag, data_length", TEST_LENGTH_DICT)
def test_calculate_data_length_from_flag(flag, data_length):
    assert data_length == calculate_data_length_from_flag(flag)
