import itertools
import collections
import logging
from typing import Deque, Union

from velbustcp.lib.consts import STX


class PacketBuffer:
    """Packet buffer.
    """

    def __init__(self):
        """Initialises the packet buffer.
        """

        self.buffer: Deque[int] = collections.deque(maxlen=10000)
        self.logger = logging.getLogger("__main__." + __name__)

    def __len__(self) -> int:
        """Return the number of items in the buffer.

        Returns:
            int: The number of items in the buffer.
        """

        return len(self.buffer)

    def __getitem__(self, key) -> Union[bytearray, int]:
        """[summary]

        Args:
            key ([type]): [description]

        Returns:
            int: [description]
        """

        if isinstance(key, slice):
            return bytearray(itertools.islice(self.buffer, key.start, key.stop - key.start, key.step))

        return int(self.buffer[key])

    def realign(self) -> None:
        """Realigns buffer by shifting the queue until the next STX or until the buffer runs out.
        """

        amount = 1

        while (amount < len(self.buffer)) and (self.buffer[amount] != STX):
            amount += 1

        self.logger.debug(f"Realigning |:{list(self.buffer)}:|")
        self.shift(amount)
        self.logger.debug(f"Realigned  |:{list(self.buffer)}:|")

    def shift(self, amount: int) -> None:
        """Shifts the buffer by the specified amount.

        Args:
            amount (int): The amount of bytes that the buffer needs to be shifted.
        """

        for _ in itertools.repeat(None, amount):
            self.buffer.popleft()

    def feed(self, data: bytearray) -> None:
        """Feed data into the parser to be processed.

        Args:
            array (bytearray): The data that will be added to the parser.
        """

        self.buffer.extend(data)
