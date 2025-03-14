import asyncio
import ssl
import logging
from typing import List, Optional
from velbustcp.lib.connection.tcp.client import Client
from velbustcp.lib.connection.tcp.clientconnection import ClientConnection
from velbustcp.lib.settings.network import NetworkSettings
from velbustcp.lib.signals import on_client_close


class Network:

    def __init__(self, options: NetworkSettings):
        """Initialises a TCP network.

        Args:
            options (NetworkSettings): The options used to configure the network.
        """

        self.__logger: logging.Logger = logging.getLogger("__main__." + __name__)
        self.__clients: List[Client] = []
        self.__options: NetworkSettings = options
        self.__context: Optional[ssl.SSLContext] = None
        self.__server: Optional[asyncio.AbstractServer] = None

        # Hook up signal
        def handle_client_close(sender: Client, **kwargs):
            self.__logger.info("TCP connection closed %s", sender.address())

            if sender not in self.__clients:
                return

            self.__clients.remove(sender)
        self.handle_client_close = handle_client_close
        on_client_close.connect(handle_client_close)

    async def start(self) -> None:
        """Starts up the TCP server
        """

        if self.__options.ssl:
            self.__context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
            self.__context.load_cert_chain(self.__options.cert, keyfile=self.__options.pk)

        self.__server = await asyncio.start_server(
            self.__handle_client,
            self.__options.host,
            self.__options.port,
            ssl=self.__context
        )

        self.__logger.info(f"Listening to TCP connections on {self.__options.address} [SSL:{self.__options.ssl}] [AUTH:{self.__options.auth}]")

    async def stop(self) -> None:
        """Stops the TCP server
        """

        if self.__server is not None:
            self.__server.close()
            await self.__server.wait_closed()
            self.__server = None

        for client in self.__clients:
            await client.stop()

        self.__clients.clear()
        self.__logger.info("Stopped TCP connection %s", self.__options.address)

    async def __handle_client(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        """Handles a new client connection
        """

        connection = ClientConnection()
        connection.reader = reader
        connection.writer = writer
        connection.should_authorize = self.__options.auth
        connection.authorization_key = self.__options.auth_key

        client = Client(connection)
        self.__clients.append(client)
        await client.start()

    async def send(self, data: bytearray) -> None:
        """Sends given data to all connected clients to the network.

        Args:
            data (bytearray): Specifies the packet to send to the connected clients of this network.
        """

        if not self.__options.relay:
            return

        if self.__logger.isEnabledFor(logging.DEBUG):  # pragma: no cover
            self.__logger.debug("[TCP OUT] %s", " ".join(hex(x) for x in data))

        tasks = [client.send(data) for client in self.__clients]
        await asyncio.gather(*tasks)