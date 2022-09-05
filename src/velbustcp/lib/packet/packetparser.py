import logging
from typing import List, Optional

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
        self.logger = logging.getLogger("__main__." + __name__)

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

    def __extract(self) -> Optional[bytearray]:
        """Checks whether or not the parser has a valid packet in its buffer.

        Returns:
            bool: A boolean indicating whether or not the parser has a valid packet in its buffer.
        """

        # Shortcut if we don't have enough bytes in the buffer to have a valid packet
        if len(self.buffer) < consts.MIN_PACKET_LENGTH:
            return None

        body_length = self.buffer[3] & consts.LENGTH_MASK
        packet_length = consts.MIN_PACKET_LENGTH + body_length

        # Shortcut if we don't have enough bytes to complete the packet length specified in body
        if len(self.buffer) < packet_length:
            return None

        start_valid = self.buffer[0] == consts.STX
        priority_valid = self.buffer[1] in consts.PRIORITIES
        checksum_valid = self.buffer[packet_length - 2] == self.checksum(self.buffer[0: 4 + body_length])
        end_valid = self.buffer[packet_length - 1] == consts.ETX

        if not (start_valid and priority_valid and checksum_valid and end_valid):
            return None

        packet = self.buffer[0: packet_length]
        self.buffer.shift(packet_length)

        return packet

    def __has_enough_bytes_for_new_packet(self) -> bool:
        """Determines if there are enough bytes in the buffer for a packet to be parsed.

        Returns:
            bool: Whether or not there are enough bytes in the buffer.
        """

        # Make sure we have the minimal packet length waiting in buffer
        if len(self.buffer) < consts.MIN_PACKET_LENGTH:
            return False

        # Return whether or not we have a full packet body's worth of packets waiting
        body_length = self.buffer[3] & consts.LENGTH_MASK
        packet_length = consts.MIN_PACKET_LENGTH + body_length
        return len(self.buffer) >= packet_length

    def feed(self, array: bytearray) -> List[bytearray]:
        """Feed data into the parser to be processed.

        Args:
            array (bytearray): The data that will be added to the parser.
        """

        self.buffer.feed(array)
        packets = []

        while self.__has_enough_bytes_for_new_packet():

            # Do we straight up have a valid packet?
            packet = self.__extract()
            if packet:
                packets.append(packet)

            # Is the buffer full enough to realign?
            else:
                self.buffer.realign()

        return packets
