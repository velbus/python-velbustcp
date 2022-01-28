import sys

if sys.version_info >= (3, 8):
    from typing import Protocol
else:  # pragma: no cover
    from typing_extensions import Protocol


class OnBusPacketReceived(Protocol):
    def __call__(self, packet_id: str) -> None:
        pass


class OnBusPacketSent(Protocol):
    def __call__(self, packet_id: str) -> None:
        pass


class OnBusError(Protocol):
    def __call__(self) -> None:
        pass
