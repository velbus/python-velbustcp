
import pytest

from pytest_mock import MockerFixture
from velbustcp.lib.connection.bridge import Bridge
from velbustcp.lib.consts import COMMAND_BUS_ACTIVE, COMMAND_BUS_BUFFERREADY, COMMAND_BUS_OFF, ETX, PRIORITY_HIGH, STX

BUS_ACTIVE_DATA = bytearray([ETX, PRIORITY_HIGH, 0x00, 0x01, COMMAND_BUS_ACTIVE, 0x00, STX])
BUS_OFF_DATA = bytearray([ETX, PRIORITY_HIGH, 0x00, 0x01, COMMAND_BUS_OFF, 0x00, STX])
BUS_BUFFER_READY_DATA = bytearray([ETX, PRIORITY_HIGH, 0x00, 0x01, COMMAND_BUS_BUFFERREADY, 0x00, STX])


@pytest.mark.asyncio
async def test_bridge_start(mocker: MockerFixture):
    mock_bus = mocker.AsyncMock()
    mock_network_manager = mocker.AsyncMock()

    bridge = Bridge(mock_bus, mock_network_manager)
    await bridge.start()

    mock_bus.ensure.assert_called()
    mock_network_manager.start.assert_called()


@pytest.mark.asyncio
async def test_bridge_stop(mocker: MockerFixture):
    mock_bus = mocker.AsyncMock()
    mock_network_manager = mocker.AsyncMock()

    bridge = Bridge(mock_bus, mock_network_manager)
    await bridge.stop()

    mock_bus.stop.assert_called()
    mock_network_manager.stop.assert_called()
