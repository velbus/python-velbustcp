import socket

class ClientConnection():
    """Represents an incoming client connection.
    """
    
    socket: socket.socket
    should_authorize: bool
    authorization_key: str