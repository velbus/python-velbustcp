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
