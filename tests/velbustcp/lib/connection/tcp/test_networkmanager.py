from pytest_mock import MockFixture
from velbustcp.lib import consts
from velbustcp.lib.connection.tcp.client import Client
from velbustcp.lib.connection.tcp.network import Network

from velbustcp.lib.connection.tcp.networkmanager import NetworkManager
from velbustcp.lib.packet.packetcache import PacketCache


def test_add_network(mocker: MockFixture):

    # Arrange
    network_manager = NetworkManager()
    network = mocker.Mock(spec=Network)

    # Act
    network_manager.add_network(network)

    # Assert
    assert network.on_packet_received


def test_start(mocker: MockFixture):

    # Arrange
    network_manager = NetworkManager()
    network = mocker.Mock(spec=Network)
    network_manager.add_network(network)

    # Act
    network_manager.start()

    # Assert
    network.start.assert_called_once()


def test_stop(mocker: MockFixture):

    # Arrange
    network_manager = NetworkManager()
    network = mocker.Mock(spec=Network)
    network_manager.add_network(network)

    # Act
    network_manager.stop()

    # Assert
    network.stop.assert_called_once()


def test_send(mocker: MockFixture):

    # Arrange
    packet = bytearray([0x01])
    cache = PacketCache()
    packet_id = cache.add(packet)
    network_manager = NetworkManager()
    network = mocker.Mock(spec=Network)
    network_manager.add_network(network)

    # Act
    network_manager.send(packet_id)

    # Assert
    network.send.assert_called_once_with(packet, None)


def test_receive_from_client_with_send(mocker: MockFixture):

    # Arrange
    def on_receive(packet_id: str):
        network_manager.send(packet_id)

    packet = bytearray([0x01])
    client = mocker.Mock(spec=Client)
    network = mocker.Mock(spec=Network)
    network_manager = NetworkManager()
    network_manager.add_network(network)
    network_manager.on_packet_received = on_receive

    # Act
    network.on_packet_received(client, packet)

    # Assert
    network.send.assert_called_with(packet, client)


def test_receive_buffer_full(mocker: MockFixture):

    # Arrange
    packet = bytearray([0x01])
    client = mocker.Mock(spec=Client)
    network = mocker.Mock(spec=Network)
    network_manager = NetworkManager()
    network_manager.add_network(network)

    # Act
    consts.MAX_BUFFER_LENGTH = 0
    network.on_packet_received(client, packet)

    # Assert
    network.send.assert_not_called()
