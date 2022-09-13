import itertools
import collections
import logging
from typing import Deque, Union, overload

from velbustcp.lib.consts import STX


class PacketBuffer:
    """Packet buffer.
    """

    def __init__(self):
        """Initialises the packet buffer.
        """

        self.__buffer: Deque[int] = collections.deque(maxlen=10000)
        self.__logger: logging.Logger = logging.getLogger("__main__." + __name__)

    def __len__(self) -> int:
        """Return the number of items in the buffer.

        Returns:
            int: The number of items in the buffer.
        """

        return len(self.__buffer)

    @overload
    def __getitem__(self, key: int) -> int:
        """..."""

    @overload
    def __getitem__(self, key: slice) -> bytearray:
        """..."""

    def __getitem__(self, item: Union[int, slice]) -> Union[int, bytearray]:
        """..."""

        if isinstance(item, slice):
            return bytearray(itertools.islice(self.__buffer, item.start, item.stop - item.start, item.step))

        return self.__buffer[item]

    def realign(self) -> None:
        """Realigns buffer by shifting the queue until the next STX or until the buffer runs out.
        """

        amount = 1

        while (amount < len(self.__buffer)) and (self.__buffer[amount] != STX):
            amount += 1

        self.shift(amount)

    def shift(self, amount: int) -> None:
        """Shifts the buffer by the specified amount.

        Args:
            amount (int): The amount of bytes that the buffer needs to be shifted.
        """

        for _ in itertools.repeat(None, amount):
            self.__buffer.popleft()

    def feed(self, data: bytearray) -> None:
        """Feed data into the parser to be processed.

        Args:
            array (bytearray): The data that will be added to the parser.
        """

        self.__buffer.extend(data)
