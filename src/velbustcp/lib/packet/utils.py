LENGTH_DICT = {
    0x09: 12,
    0x0A: 16,
    0x0B: 20,
    0x0C: 24,
    0x0D: 32,
    0x0E: 48,
    0x0F: 64
}


def calculate_data_length_from_flag(flag: int) -> int:
    """Returns the data length from given data length flag.

    Args:
        flag (int): The data length flag in the packet.

    Returns:
        int: The data length of the packet.
    """
    if flag in LENGTH_DICT:
        return LENGTH_DICT[flag]

    return flag
