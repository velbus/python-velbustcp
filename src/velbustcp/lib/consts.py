PRIORITY_HIGH = 0xF8
PRIORITY_FIRMWARE = 0xF9
PRIORITY_LOW = 0xFB
PRIORITY_THIRDPARTY = 0xFA
PRIORITIES = [PRIORITY_FIRMWARE, PRIORITY_HIGH, PRIORITY_LOW, PRIORITY_THIRDPARTY]

COMMAND_BUS_OFF = 0x09
COMMAND_BUS_ACTIVE = 0x0A
COMMAND_BUS_BUFFERFULL = 0x0B
COMMAND_BUS_BUFFERREADY = 0x0C

MAX_BUFFER_LENGTH = 292  # 292 full-sized velbus-packets (14 bytes), so 4096 bytes.

# Magic packet numbers
STX = 0x0F
ETX = 0x04
LENGTH_MASK = 0x0F
HEADER_LENGTH = 4       # Header: [STX, priority, address, RTR+data length]
MAX_DATA_AMOUNT = 8     # Maximum amount of data bytes in a packet
MIN_PACKET_LENGTH = 6   # Smallest possible packet: [STX, priority, address, RTR+data length, CRC, ETC]
