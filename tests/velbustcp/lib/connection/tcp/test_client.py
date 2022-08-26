import threading
from velbustcp.lib.connection.tcp.client import Client
from pytest_mock import MockFixture, MockerFixture
from velbustcp.lib.connection.tcp.clientconnection import ClientConnection
from velbustcp.lib.signals import on_client_close, on_tcp_receive


def get_mock_socket(mocker: MockerFixture):

    def get_address():
        return "mock"

    socket = mocker.Mock()
    socket.getpeername = get_address

    return socket


def test_defaults(mocker: MockerFixture):

    # Create connection
    conn = ClientConnection()
    conn.socket = get_mock_socket(mocker)

    # Create client
    client = Client(conn)

    # Check if address is correct
    assert client.address() == "mock"

    # Check if not active
    assert not client.is_active()


def test_auth_wrong_key(mocker: MockerFixture):

    # Create connection
    def recv(len):
        return "velbus".encode("utf-8")

    conn = ClientConnection()
    conn.socket = get_mock_socket(mocker)
    conn.socket.recv = recv
    conn.should_authorize = True
    conn.authorization_key = "something-different"

    # Create client
    e = threading.Event()

    def handle_client_close(sender, **kwargs):
        e.set()
    on_client_close.connect(handle_client_close)   

    client = Client(conn)
    client.start()

    e.wait()
    assert not client.is_active()


def test_auth_no_data(mocker: MockerFixture):

    # Create connection
    def recv(len):
        return bytes()

    conn = ClientConnection()
    conn.socket = get_mock_socket(mocker)
    conn.socket.recv = recv
    conn.should_authorize = True
    conn.authorization_key = "velbus"

    # Create client
    e = threading.Event()

    def handle_client_close(sender, **kwargs):
        e.set()
    on_client_close.connect(handle_client_close)   

    client = Client(conn)
    client.start()

    e.wait()
    assert not client.is_active()


def test_auth_recv_exception(mocker: MockerFixture):

    # Create connection
    def recv(len):
        raise Exception("Thrown on purpose")

    conn = ClientConnection()
    conn.socket = get_mock_socket(mocker)
    conn.socket.recv = recv
    conn.should_authorize = True
    conn.authorization_key = "velbus"

    # Create client
    e = threading.Event()

    def handle_client_close(sender, **kwargs):
        e.set()
    on_client_close.connect(handle_client_close)   

    client = Client(conn)
    client.start()

    e.wait()
    assert not client.is_active()


def test_packet_empty(mocker: MockFixture):

    # Create connection
    def recv(len):
        return bytes()

    conn = ClientConnection()
    conn.socket = get_mock_socket(mocker)
    conn.socket.recv = recv
    conn.should_authorize = False

    # Create client
    e = threading.Event()
    def handle_client_close(sender, **kwargs):
        e.set()
    on_client_close.connect(handle_client_close)   

    client = Client(conn)
    client.start()

    e.wait()
    assert not client.is_active()


def test_packet_handling(mocker: MockFixture):

    # Create connection
    data = bytes([0x0F, 0xFB, 0xFF, 0x40, 0xB7, 0x04])

    def recv(len):
        return data

    conn = ClientConnection()
    conn.socket = get_mock_socket(mocker)
    conn.socket.recv = recv
    conn.should_authorize = False

    # Create client
    e = threading.Event()

    def on_packet_receive(sender, **kwargs):
        packet = kwargs["packet"]
        if (packet == bytearray(data)):
            e.set()

    client = Client(conn)
    client.start()

    on_tcp_receive.connect(on_packet_receive)

    e.wait()

    client.stop()
    assert not client.is_active()


def test_packet_recv_exception(mocker: MockerFixture):

    # Create connection
    def recv(len):
        raise Exception("Thrown on purpose")

    conn = ClientConnection()
    conn.socket = get_mock_socket(mocker)
    conn.socket.recv = recv
    conn.should_authorize = False

    # Create client
    e = threading.Event()

    def handle_client_close(sender, **kwargs):
        e.set()
    on_client_close.connect(handle_client_close)   

    client = Client(conn)
    client.start()

    e.wait()
    assert not client.is_active()


def test_client_send(mocker: MockerFixture):

    # Create connection
    data = bytes([0x0F, 0xFB, 0xFF, 0x40, 0xB7, 0x04])

    def recv(len):
        return [0x00]

    conn = ClientConnection()
    conn.socket = get_mock_socket(mocker)
    conn.socket.recv = recv
    conn.should_authorize = False

    # Create client
    client = Client(conn)

    # First send data without client being connected
    client.send(data)
    conn.socket.sendall.assert_not_called()

    # Start client and try sending
    client.start()
    client.send(bytearray(data))
    conn.socket.sendall.assert_called_with(data)
    client.stop()

def test_client_send_not_own_packet(mocker: MockerFixture):

    # Create connection
    data = bytes([0x0F, 0xFB, 0xFF, 0x40, 0xB7, 0x04])

    def recv(len):
        return data

    conn = ClientConnection()
    conn.socket = get_mock_socket(mocker)
    conn.socket.recv = recv
    conn.should_authorize = False

    # Create client
    client = Client(conn)

    # Start client and try sending
    # should fail because it originated from that client
    client.start()
    client.send(bytearray(data))
    conn.socket.sendall.assert_not_called()
    client.stop()