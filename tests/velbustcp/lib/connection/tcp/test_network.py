from pytest_mock import MockFixture

from velbustcp.lib.connection.tcp.network import Network
from velbustcp.lib.settings.network import NetworkSettings


def test_defaults(mocker: MockFixture):

    # Arrange
    settings = NetworkSettings()
    network = Network(options=settings)

    # Assert
    assert not network.is_active()


def test_start_stop(mocker: MockFixture):

    # Arrange
    settings = NetworkSettings()
    network = Network(options=settings)

    # Act
    network.start()

    # Assert
    assert network.is_active()
    network.stop()
    assert not network.is_active()


def test_send_not_active(mocker: MockFixture):

    # Arrange
    settings = NetworkSettings()
    network = Network(options=settings)
    spy = mocker.spy(network, 'is_active')

    # Act
    network.send(bytearray([]))

    # Assert
    spy.assert_called_once()
    assert not spy.spy_return
