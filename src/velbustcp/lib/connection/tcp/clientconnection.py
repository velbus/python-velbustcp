import asyncio

class ClientConnection:
    """Represents an incoming client connection.
    """

    reader: asyncio.StreamReader
    writer: asyncio.StreamWriter
    should_authorize: bool = False
    authorization_key: str = ""