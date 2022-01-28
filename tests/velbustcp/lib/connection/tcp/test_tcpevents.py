from velbustcp.lib.connection.tcp.client import Client
from velbustcp.lib.connection.tcp.events import OnNetworkManagerPacketReceived, OnNetworkPacketReceived


def test_events():
    e: OnNetworkManagerPacketReceived = on_network_manager_packet_received
    e("abc")

    e: OnNetworkPacketReceived = on_network_packet_received
    e(None, None)


def on_network_packet_received(client: Client, packet: bytearray):
    pass


def on_network_manager_packet_received(packet_id: str):
    pass
