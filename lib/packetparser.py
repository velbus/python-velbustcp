import collections
import itertools

from . import consts

# Magic packet numbers
STX                 = 0x0F
ETX                 = 0x04
LENGTH_MASK         = 0x0F
HEADER_LENGTH       = 4         # Header: [STX, priority, address, RTR+data length]
MAX_DATA_AMOUNT     = 8         # Maximum amount of data bytes in a packet
MIN_PACKET_LENGTH   = 6         # Smallest possible packet: [STX, priority, address, RTR+data length, CRC, ETC]

class PacketParser:
    """
    Packet parser for the Velbus protocol.
    The packet protocol is detailed at https://github.com/velbus/packetprotocol.
    """

    def __init__(self):
        """
        Initialises the packet parser.
        """

        self.buffer = collections.deque(maxlen=10000)

    def __realign_buffer(self):
        """
        Realigns buffer by shifting the queue until the next STX or until the buffer runs out.
        """

        amount = 1

        while (amount < len(self.buffer)) and (self.buffer[amount] != STX):
            amount += 1

        self.__shift_buffer(amount)

    def __shift_buffer(self, amount):
        """
        Shifts the buffer by the specified amount.

        :param amount: The amount of bytes that the buffer needs to be shifted.
        """

        assert isinstance(amount, int)

        for _ in itertools.repeat(None, amount):
            self.buffer.popleft()

    def __has_valid_header_waiting(self):
        """
        Checks whether or not the parser has a valid packet header waiting.

        :return: A boolean indicating whether or not the parser has a valid packet header waiting.
        """

        # Shortcut if the buffer isn't large enough to have a header
        if len(self.buffer) < HEADER_LENGTH:
            return False

        start_valid      = self.buffer[0] == STX
        bodysize_valid   = self.__curr_packet_body_length() <= MAX_DATA_AMOUNT
        priority_valid   = self.buffer[1] in consts.PRIORITIES

        return start_valid and bodysize_valid and priority_valid

    @staticmethod
    def checksum(arr):
        """
        Calculate checksum of the given array.
		The checksum is calculated by summing all values in an array, then performing the two's complement.

        :param arr: The array of bytes of which the checksum has to be calculated of.
        :return: The checksum of the given array.
        """

        assert isinstance(arr, bytearray)

        crc = sum(arr)
        crc = crc ^ 0xFF
        crc = crc + 1
        crc = crc & 0xFF

        return crc

    def __has_valid_packet_waiting(self):
        """
        Checks whether or not the parser has a valid packet in its buffer.

        :return: A boolean indicating whether or not the parser has a valid packet in its buffer.
        """

        # Make sure that the header in the packet is valid
        if not self.__has_valid_header_waiting():
            return False

        # Shortcut if we don't have enough bytes in the buffer to have a valid packet
        if len(self.buffer) < MIN_PACKET_LENGTH:
            return False
      
        # Shortcut if we don't have enough bytes to complete the packet length specified in body
        if not self.__has_packet_length_waiting():
            return False

        bytes_to_check  = bytearray(itertools.islice(self.buffer, 0, 4 + self.__curr_packet_body_length()))
        checksum_valid  = self.buffer[self.__curr_packet_length() - 2] == self.checksum(bytes_to_check)
        end_valid       = self.buffer[self.__curr_packet_length() - 1] == ETX

        return checksum_valid and end_valid

    def __has_packet_length_waiting(self):
        """
        Checks whether the current packet has the full length's worth of data waiting in the buffer.
        This should only be called when __has_valid_header_waiting() returns True.
        """

        return len(self.buffer) >= self.__curr_packet_length()

    def __curr_packet_length(self):
        """
        Gets the current waiting packet's total length.
        This should only be called when __has_valid_header_waiting() returns True.

        :return: The current waiting packet's total length.
        """

        return MIN_PACKET_LENGTH + self.__curr_packet_body_length()

    def __curr_packet_body_length(self):
        """
        Gets the current waiting packet's body length.
        This should only be called when __has_valid_header_waiting() returns True.

        :return: The current waiting packet's body length.
        """

        return self.buffer[3] & LENGTH_MASK

    def __extract_packet(self):
        """
        Extracts a packet from the buffer and shifts it.
        Make sure this is only called after __has_valid_packet_waiting() return True.

        :return: A bytearray with the currently waiting packet.
        """

        length = self.__curr_packet_length()
        packet = bytearray(itertools.islice(self.buffer, 0, length))
        self.__shift_buffer(length)

        return packet

    def feed(self, array):
        """
        Feed data into the parser to be processed.

        :param array: The data that will be added to the parser.
        """
        
        assert isinstance(array, bytearray)

        self.buffer.extend(array)

    def next(self):
        """
        Attempts to get a packet from the parser.
        This is a safe operation if there are no packets waiting in the parser.

        :return: Will return a bytearray if there is a packet present, None if there is no packet available.
        """

        packet = None

        # Check if we have a valid packet until we don't have anything left in buffer
        has_valid_packet = self.__has_valid_packet_waiting()
        while (not has_valid_packet) and (len(self.buffer) > HEADER_LENGTH) and self.__has_packet_length_waiting():
            self.__realign_buffer()
            has_valid_packet = self.__has_valid_packet_waiting()

        # If we have a valid packet, extract it
        if has_valid_packet:
            packet = self.__extract_packet()   

        return packet