from velbustcp.lib.connection.serial.events import OnBusError, OnBusPacketReceived, OnBusPacketSent


def test_events():

    e: OnBusPacketReceived = on_bus_packet_received
    e("test")

    e: OnBusPacketSent = on_bus_packet_sent
    e("test")

    e: OnBusError = on_bus_error
    e()


def on_bus_packet_received(packet_id: str) -> None:
    pass


def on_bus_packet_sent(packet_id: str) -> None:
    pass


def on_bus_error() -> None:
    pass
