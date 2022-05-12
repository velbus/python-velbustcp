import sys

if sys.version_info >= (3, 8):  # pragma: no cover
    from typing import Protocol
else:  # pragma: no cover
    from typing_extensions import Protocol

from velbustcp.lib.connection.tcp.client import Client


class OnNetworkPacketReceived(Protocol):
    def __call__(self, client: Client, packet: bytearray) -> None:
        pass  # pragma: no cover


class OnNetworkManagerPacketReceived(Protocol):
    def __call__(self, packet_id: str) -> None:
        pass  # pragma: no cover
