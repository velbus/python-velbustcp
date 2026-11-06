import asyncio
import errno
import pytest
from pytest_mock import MockFixture

from velbustcp.lib.connection.tcp.network import Network
from velbustcp.lib.settings.network import NetworkSettings


def test_defaults(mocker: MockFixture):

    # Arrange
    settings = NetworkSettings()
    network = Network(options=settings)

    # Assert
    assert not network.is_active()


@pytest.mark.asyncio
async def test_start_stop(mocker: MockFixture):

    # Arrange
    settings = NetworkSettings()
    network = Network(options=settings)

    # Act
    start_task = asyncio.create_task(network.start())
    await asyncio.sleep(1)  # Allow some time for the server to start

    # Assert
    assert network.is_active()

    # Cleanup
    await network.stop()
    assert not network.is_active()
    start_task.cancel()
    try:
        await start_task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_send_not_active(mocker: MockFixture):

    # Arrange
    settings = NetworkSettings()
    network = Network(options=settings)
    spy = mocker.spy(network, 'is_active')

    # Act
    await network.send(bytearray([]))

    # Assert
    spy.assert_called_once()
    assert not spy.spy_return


@pytest.mark.asyncio
@pytest.mark.parametrize("error", [
    ConnectionResetError(104, "Connection reset by peer"),
    OSError(errno.EHOSTUNREACH, "No route to host"),
    RuntimeError("Thrown on purpose"),
])
async def test_send_client_failure(mocker: MockFixture, error: Exception):

    # Arrange
    network = Network(options=NetworkSettings())
    mocker.patch.object(network, 'is_active', return_value=True)

    failing = mocker.Mock()
    failing.send = mocker.AsyncMock(side_effect=error)
    healthy = mocker.Mock()
    healthy.send = mocker.AsyncMock()
    network._Network__clients = [failing, healthy]  # type: ignore[attr-defined]

    data = bytearray([0x0F])

    # Act, must not raise
    await network.send(data)

    # Assert, the healthy client still got the data
    failing.send.assert_awaited_once_with(data)
    healthy.send.assert_awaited_once_with(data)
