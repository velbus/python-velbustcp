import logging
from typing import Optional

from velbustcp.lib import consts
from velbustcp.lib.packet.packetbuffer import PacketBuffer


class PacketParser:
    """Packet parser for the Velbus protocol.
    The packet protocol is detailed at https://github.com/velbus/packetprotocol.
    """

    def __init__(self):
        """Initialises the packet parser.
        """

        self.buffer: PacketBuffer = PacketBuffer()
        self.logger = logging.getLogger(__name__)

    def __has_valid_header_waiting(self) -> bool:
        """Checks whether or not the parser has a valid packet header waiting.

        Returns:
            bool: A boolean indicating whether or not the parser has a valid packet header waiting.
        """

        # Shortcut if the buffer isn't filled enough to have a header
        if not self.__has_header_length():
            return False

        start_valid = self.buffer[0] == consts.STX
        bodysize_valid = self.__curr_packet_body_length() <= consts.MAX_DATA_AMOUNT
        priority_valid = self.buffer[1] in consts.PRIORITIES

        return start_valid and bodysize_valid and priority_valid

    def __has_header_length(self) -> bool:
        """Determines if the buffer has enough data to have a header waiting.

        Returns:
            bool: Whether or not the buffer has enough data to have a header waiting.
        """

        return len(self.buffer) >= consts.HEADER_LENGTH

    @staticmethod
    def checksum(arr: bytearray) -> int:
        """ Calculate checksum of the given array.
        The checksum is calculated by summing all values in an array, then performing the two's complement.

        Args:
            arr (bytearray): The array of bytes of which the checksum has to be calculated of.

        Returns:
            int: The checksum of the given array.
        """

        crc = sum(arr)
        crc = crc ^ 0xFF
        crc = crc + 1
        crc = crc & 0xFF

        return crc

    def __has_valid_packet_waiting(self) -> bool:
        """Checks whether or not the parser has a valid packet in its buffer.

        Returns:
            bool: A boolean indicating whether or not the parser has a valid packet in its buffer.
        """

        # Make sure that the header in the packet is valid
        if not self.__has_valid_header_waiting():
            return False

        # Shortcut if we don't have enough bytes in the buffer to have a valid packet
        if len(self.buffer) < consts.MIN_PACKET_LENGTH:
            return False

        # Shortcut if we don't have enough bytes to complete the packet length specified in body
        if not self.__has_packet_length_waiting():
            return False

        bytes_to_check = bytearray(self.buffer[0: 4 + self.__curr_packet_body_length()])
        checksum_valid = self.buffer[self.__curr_packet_length() - 2] == self.checksum(bytes_to_check)
        end_valid = self.buffer[self.__curr_packet_length() - 1] == consts.ETX

        return checksum_valid and end_valid

    def __has_packet_length_waiting(self) -> bool:
        """Checks whether the current packet has the full length's worth of data waiting in the buffer.
        This should only be called when __has_valid_header_waiting() returns True.

        Returns:
            bool: Whether or not the buffer has at least the packet length available.
        """

        return len(self.buffer) >= self.__curr_packet_length()

    def __curr_packet_length(self) -> int:
        """Gets the current waiting packet's total length.
        This should only be called when __has_valid_header_waiting() returns True.

        Returns:
            int: The current waiting packet's total length.
        """

        return consts.MIN_PACKET_LENGTH + self.__curr_packet_body_length()

    def __curr_packet_body_length(self) -> int:
        """Gets the current waiting packet's body length.
        This should only be called when __has_header_length() returns True.

        Returns:
            int: The current waiting packet's body length.
        """

        return int(self.buffer[3]) & consts.LENGTH_MASK

    def __extract_packet(self) -> bytearray:
        """Extracts a packet from the buffer and shifts it.
        Make sure this is only called after __has_valid_packet_waiting() return True.

        Returns:
            bytearray: A bytearray with the currently waiting packet.
        """

        length = self.__curr_packet_length()
        packet = bytearray(self.buffer[0: length])
        self.buffer.shift(length)

        return packet

    def feed(self, array: bytearray) -> None:
        """Feed data into the parser to be processed.

        Args:
            array (bytearray): The data that will be added to the parser.
        """

        self.buffer.feed(array)

    def next(self) -> Optional[bytearray]:
        """Attempts to get a packet from the parser.
        This is a safe operation if there are no packets waiting in the parser.

        Returns:
            bytearray: Will return a bytearray if there is a packet present, None if there is no packet available.
        """

        packet = None

        # Check if we have a valid packet until we don't have anything left in buffer
        has_valid_packet = self.__has_valid_packet_waiting()

        while (not has_valid_packet) and self.__has_header_length():
            self.buffer.realign()
            has_valid_packet = self.__has_valid_packet_waiting()

        # If we have a valid packet, extract it
        if has_valid_packet:
            packet = self.__extract_packet()

        return packet
