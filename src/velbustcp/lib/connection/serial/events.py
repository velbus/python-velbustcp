from typing import Protocol


class OnBusPacketReceived(Protocol):
    def __call__(self, packet: bytearray) -> None:
        pass

class OnBusPacketSent(Protocol):
    def __call__(self, packet_id: str) -> None:
        pass

class OnBusError(Protocol):
    def __call__(self) -> None:
        pass

