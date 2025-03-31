import pytest
from pytest_mock import MockFixture
from velbustcp.lib.connection.tcp.network import Network
from velbustcp.lib.connection.tcp.networkmanager import NetworkManager


@pytest.mark.asyncio
async def test_start(mocker: MockFixture):
    # Arrange
    network_manager = NetworkManager()
    network = mocker.Mock(spec=Network)
    network_manager.add_network(network)

    # Act
    await network_manager.start()

    # Assert
    network.start.assert_called_once()


@pytest.mark.asyncio
async def test_stop(mocker: MockFixture):
    # Arrange
    network_manager = NetworkManager()
    network = mocker.Mock(spec=Network)
    network_manager.add_network(network)

    # Act
    await network_manager.stop()

    # Assert
    network.stop.assert_called_once()


@pytest.mark.asyncio
async def test_send(mocker: MockFixture):
    # Arrange
    packet = bytearray([0x01])
    network_manager = NetworkManager()
    network = mocker.Mock(spec=Network)
    network_manager.add_network(network)

    # Act
    await network_manager.send(packet)

    # Assert
    network.send.assert_called_once_with(packet)


@pytest.mark.asyncio
async def test_add_multiple_networks(mocker: MockFixture):
    # Arrange
    network_manager = NetworkManager()
    network1 = mocker.Mock(spec=Network)
    network2 = mocker.Mock(spec=Network)
    network_manager.add_network(network1)
    network_manager.add_network(network2)

    # Act
    await network_manager.start()

    # Assert
    network1.start.assert_called_once()
    network2.start.assert_called_once()
