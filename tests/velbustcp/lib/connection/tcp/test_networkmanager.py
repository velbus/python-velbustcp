from pytest_mock import MockFixture
from velbustcp.lib import consts
from velbustcp.lib.connection.tcp.client import Client
from velbustcp.lib.connection.tcp.network import Network

from velbustcp.lib.connection.tcp.networkmanager import NetworkManager


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
    network_manager = NetworkManager()
    network = mocker.Mock(spec=Network)
    network_manager.add_network(network)

    # Act
    network_manager.send(packet)

    # Assert
    network.send.assert_called_once_with(packet)
