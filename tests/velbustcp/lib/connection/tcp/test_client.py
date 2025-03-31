import asyncio
import threading
import pytest
from velbustcp.lib.connection.tcp.client import Client
from pytest_mock import MockFixture, MockerFixture
from velbustcp.lib.connection.tcp.clientconnection import ClientConnection
from velbustcp.lib.signals import on_client_close, on_tcp_receive


def get_mock_connection(mocker: MockerFixture):
    """Creates a mock ClientConnection with mocked reader and writer."""
    connection = mocker.Mock(spec=ClientConnection)
    connection.reader = mocker.AsyncMock()
    connection.writer = mocker.AsyncMock()
    connection.writer.get_extra_info = mocker.Mock(return_value="mock")
    return connection


def test_defaults(mocker: MockerFixture):
    # Create connection
    conn = get_mock_connection(mocker)

    # Create client
    client = Client(conn)

    # Check if address is correct
    assert client.address() == "mock"

    # Check if not active
    assert not client.is_active()


@pytest.mark.asyncio
async def test_auth_wrong_key(mocker: MockerFixture):
    # Create connection
    conn = get_mock_connection(mocker)
    conn.reader.read = mocker.AsyncMock(return_value="velbus".encode("utf-8"))
    conn.should_authorize = True
    conn.authorization_key = "something-different"

    # Create client
    e = asyncio.Event()

    def handle_client_close(sender, **kwargs):
        e.set()

    on_client_close.connect(handle_client_close)

    client = Client(conn)
    task = asyncio.create_task(client.start())  # Run client.start() as a separate task

    await e.wait()  # Wait for the event to be set

    await client.stop()
    await task

    assert not client.is_active()


@pytest.mark.asyncio
async def test_auth_no_data(mocker: MockerFixture):
    # Create connection
    conn = get_mock_connection(mocker)
    conn.reader.read = mocker.AsyncMock(return_value=b"")
    conn.should_authorize = True
    conn.authorization_key = "velbus"

    # Create client
    e = asyncio.Event()

    def handle_client_close(sender, **kwargs):
        e.set()

    on_client_close.connect(handle_client_close)

    client = Client(conn)
    task = asyncio.create_task(client.start())  # Run client.start() as a separate task

    await e.wait()  # Wait for the event to be set

    await client.stop()
    await task

    assert not client.is_active()


@pytest.mark.asyncio
async def test_auth_recv_exception(mocker: MockerFixture):
    # Create connection
    conn = get_mock_connection(mocker)
    conn.reader.read = mocker.AsyncMock(side_effect=Exception("Thrown on purpose"))
    conn.should_authorize = True
    conn.authorization_key = "velbus"

    # Create client
    e = asyncio.Event()

    def handle_client_close(sender, **kwargs):
        e.set()

    on_client_close.connect(handle_client_close)

    client = Client(conn)
    task = asyncio.create_task(client.start())  # Run client.start() as a separate task

    await e.wait()  # Wait for the event to be set

    await client.stop()
    await task

    assert not client.is_active()


@pytest.mark.asyncio
async def test_packet_empty(mocker: MockFixture):
    # Create connection
    conn = get_mock_connection(mocker)
    conn.reader.read = mocker.AsyncMock(return_value=b"")
    conn.should_authorize = False

    # Create client
    e = asyncio.Event()

    def handle_client_close(sender, **kwargs):
        e.set()

    on_client_close.connect(handle_client_close)

    client = Client(conn)
    task = asyncio.create_task(client.start())  # Run client.start() as a separate task

    await e.wait()  # Wait for the event to be set

    await client.stop()
    await task

    assert not client.is_active()


@pytest.mark.asyncio
async def test_packet_handling(mocker: MockFixture):
    # Create connection
    data = bytes([0x0F, 0xFB, 0xFF, 0x40, 0xB7, 0x04])
    conn = get_mock_connection(mocker)
    conn.reader.read = mocker.AsyncMock(return_value=data)
    conn.should_authorize = False

    # Create client
    e = asyncio.Event()

    def on_packet_receive(sender, **kwargs):
        packet = kwargs["packet"]
        if packet == bytearray(data) and not e.is_set():
            e.set()

    on_tcp_receive.connect(on_packet_receive)

    client = Client(conn)
    task = asyncio.create_task(client.start())  # Run client.start() as a separate task

    await e.wait()  # Wait for the event to be set

    await client.stop()
    await task

    await client.stop()
    assert not client.is_active()


@pytest.mark.asyncio
async def test_packet_recv_exception(mocker: MockerFixture):
    # Create connection
    conn = get_mock_connection(mocker)
    conn.reader.read = mocker.AsyncMock(side_effect=Exception("Thrown on purpose"))
    conn.should_authorize = False

    # Create client
    e = asyncio.Event()

    def handle_client_close(sender, **kwargs):
        e.set()

    on_client_close.connect(handle_client_close)

    client = Client(conn)
    task = asyncio.create_task(client.start())  # Run client.start() as a separate task

    await e.wait()  # Wait for the event to be set

    await client.stop()
    await task

    assert not client.is_active()

@pytest.mark.asyncio
async def test_client_send(mocker: MockerFixture):
    # Create connection
    data = bytes([0x0F, 0xFB, 0xFF, 0x40, 0xB7, 0x04])
    conn = get_mock_connection(mocker)
    conn.reader.read = mocker.AsyncMock(return_value=b"\x00")
    conn.should_authorize = False

    # Create client
    client = Client(conn)

    # First send data without client being connected
    await client.send(data)
    conn.writer.write.assert_not_called()

    # Start client and try sending
    task = asyncio.create_task(client.start())  # Run client.start() as a separate task
    await asyncio.sleep(0)

    await client.send(bytearray(data))
    conn.writer.write.assert_called_with(data)

    await client.stop()
    await task


@pytest.mark.asyncio
async def test_client_send_not_own_packet(mocker: MockerFixture):
    # Create connection
    data = bytes([0x0F, 0xFB, 0xFF, 0x40, 0xB7, 0x04])
    conn = get_mock_connection(mocker)
    conn.reader.read = mocker.AsyncMock(return_value=data)
    conn.should_authorize = False

    # Create client
    client = Client(conn)

    # Start client and try sending
    # should fail because it originated from that client
    task = asyncio.create_task(client.start())  # Run client.start() as a separate task
    await asyncio.sleep(0)

    await client.send(bytearray(data))
    conn.writer.write.assert_not_called()

    await client.stop()
    await task
