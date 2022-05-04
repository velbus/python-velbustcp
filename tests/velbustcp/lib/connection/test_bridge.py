
from pytest_mock import MockerFixture
from velbustcp.lib.connection.bridge import Bridge
from velbustcp.lib.consts import COMMAND_BUS_ACTIVE, COMMAND_BUS_BUFFERREADY, COMMAND_BUS_OFF, ETX, PRIORITY_HIGH, STX
from velbustcp.lib.packet.packetcache import packet_cache

BUS_ACTIVE_DATA = bytearray([ETX, PRIORITY_HIGH, 0x00, 0x01, COMMAND_BUS_ACTIVE, 0x00, STX])
BUS_OFF_DATA = bytearray([ETX, PRIORITY_HIGH, 0x00, 0x01, COMMAND_BUS_OFF, 0x00, STX])
BUS_BUFFER_READY_DATA = bytearray([ETX, PRIORITY_HIGH, 0x00, 0x01, COMMAND_BUS_BUFFERREADY, 0x00, STX])


def test_bridge_start(mocker: MockerFixture):
    mock_bus = mocker.Mock()
    mock_network_manager = mocker.Mock()
    mock_ntp = mocker.Mock()

    bridge = Bridge(mock_bus, mock_network_manager, mock_ntp)
    bridge.start()

    mock_bus.ensure.assert_called()
    mock_network_manager.start.assert_called()
    mock_ntp.start.assert_called()


def test_bridge_events_hooked(mocker: MockerFixture):
    mock_bus = mocker.Mock()
    mock_network_manager = mocker.Mock()
    mock_ntp = mocker.Mock()

    _ = Bridge(mock_bus, mock_network_manager, mock_ntp)

    assert mock_bus.on_packet_received
    assert mock_bus.on_packet_sent
    assert mock_network_manager.on_packet_received
    assert mock_ntp.on_packet_send_request


def test_bridge_stop(mocker: MockerFixture):
    mock_bus = mocker.Mock()
    mock_network_manager = mocker.Mock()
    mock_ntp = mocker.Mock()

    bridge = Bridge(mock_bus, mock_network_manager, mock_ntp)
    bridge.stop()

    mock_bus.stop.assert_called()
    mock_network_manager.stop.assert_called()
    mock_ntp.stop.assert_called()


def test_bridge_send(mocker: MockerFixture):
    mock_bus = mocker.Mock()
    mock_network_manager = mocker.Mock()
    mock_ntp = mocker.Mock()

    bridge = Bridge(mock_bus, mock_network_manager, mock_ntp)

    packet = bytearray([0x00, 0x01, 0x02])
    bridge.send(packet)

    mock_bus.send.assert_called()


def test_bus_packet_received(mocker: MockerFixture):
    mock_bus = mocker.Mock()
    mock_network_manager = mocker.Mock()
    mock_ntp = mocker.Mock()

    _ = Bridge(mock_bus, mock_network_manager, mock_ntp)

    # Add packets to the cache
    packet_bus_off_id = packet_cache.add(BUS_OFF_DATA)
    packet_bus_active_id = packet_cache.add(BUS_ACTIVE_DATA)
    packet_bus_buffer_ready_id = packet_cache.add(BUS_BUFFER_READY_DATA)

    # Check if passing bus OFF packet, the bus gets locked
    # and the network manager receives the packet
    mock_bus.on_packet_received(packet_bus_off_id)
    mock_network_manager.send.assert_called_with(packet_bus_off_id)
    mock_bus.lock.assert_called()

    # Check if passing bus active packet, the bus is locked
    # and the network manager receives the packet
    mock_bus.on_packet_received(packet_bus_active_id)
    mock_network_manager.send.assert_called_with(packet_bus_active_id)

    # Check if passing bus buffer ready packet, the bus is unlocked
    # and the network manager receives the packet
    mock_bus.on_packet_received(packet_bus_buffer_ready_id)
    mock_network_manager.send.assert_called_with(packet_bus_buffer_ready_id)
    mock_bus.unlock.assert_called()


def test_bus_packet_sent(mocker: MockerFixture):
    mock_bus = mocker.Mock()
    mock_network_manager = mocker.Mock()
    mock_ntp = mocker.Mock()

    _ = Bridge(mock_bus, mock_network_manager, mock_ntp)

    # Add a packet to the cache
    packet_id = packet_cache.add(bytearray([]))

    # Check on bus sent, network manager recieves it too
    mock_bus.on_packet_sent(packet_id)
    mock_network_manager.send.assert_called_with(packet_id)


def test_network_packet_receive(mocker: MockerFixture):

    def not_active():
        return False

    def active():
        return True

    mock_bus = mocker.Mock()
    mock_network_manager = mocker.Mock()
    mock_ntp = mocker.Mock()

    _ = Bridge(mock_bus, mock_network_manager, mock_ntp)

    # Add a packet to the cache
    packet_id = packet_cache.add(bytearray([]))

    # Check on network receive but bus not active
    mock_bus.is_active = not_active
    mock_network_manager.on_packet_received(packet_id)
    mock_bus.send.assert_not_called()

    # Check on network receive and bus is active
    mock_bus.is_active = active
    mock_network_manager.on_packet_received(packet_id)
    mock_bus.send.assert_called_with(packet_id)
