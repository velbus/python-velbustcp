import sys

if sys.version_info >= (3, 8):
    from typing import Protocol
else:
    from typing_extensions import Protocol

from velbustcp.lib.connection.tcp.client import Client


class OnNetworkPacketReceived(Protocol):
    def __call__(self, client: Client, packet: bytearray) -> None:
        pass

class OnNetworkManagerPacketReceived(Protocol):
    def __call__(self, packet_id: str) -> None:
        pass
