import asyncio
import logging
from typing import Any, List

from velbustcp.lib.connection.tcp.clientconnection import ClientConnection
from velbustcp.lib.packet.packetparser import PacketParser
from velbustcp.lib.signals import on_tcp_receive, on_client_close


class Client:

    def __init__(self, connection: ClientConnection):
        """Initialises a network client.

        Args:
            connection (ClientConnection): The ClientConnection for the client.
        """

        self.__logger: logging.Logger = logging.getLogger("__main__." + __name__)
        self.__connection: ClientConnection = connection
        self.__is_active: bool = False
        self.__address: str = connection.writer.get_extra_info('peername')
        self.__received_packets: List[bytearray] = []

    async def start(self) -> None:
        """Starts receiving data from the client.
        """

        if self.is_active():
            return

        self.__is_active = True
        self.__logger.info("Starting client connection for %s", self.address())

        if not await self.__handle_authorization():
            self.__logger.warning("Client authorization failed for %s", self.address())
            await self.stop()
            return

        await self.__handle_packets()

        await self.stop()

    async def stop(self) -> None:
        """Stops receiving data and disconnects from the client.
        """

        if not self.is_active():
            return

        self.__is_active = False
        self.__logger.info("Closing client connection for %s", self.address())
        self.__connection.writer.close()
        await self.__connection.writer.wait_closed()
        self.__received_packets.clear()
        on_client_close.send(self)

    async def send(self, data: bytearray) -> None:
        """Sends data to the client.

        Args:
            data (bytearray): The data to be sent.
        """

        if not self.is_active():
            return

        if data in self.__received_packets:
            self.__received_packets.remove(data)
            return

        self.__connection.writer.write(data)
        await self.__connection.writer.drain()

    def is_active(self) -> bool:
        """Returns whether the client is active for communication.
        If applicable, this also means that the client is authenticated.

        Returns:
            bool: Whether the client is active for communication.
        """

        return self.__is_active

    def address(self) -> Any:
        """Returns the address of the client.

        Returns:
            Any: The address of the client.
        """

        return self.__address

    async def __handle_authorization(self) -> bool:
        """Handles client authorization.

        Returns:
            bool: Whether or not the client is successfully authenticated.
        """

        if not self.__connection.should_authorize:
            return True

        try:
            data = await self.__connection.reader.read(1024)

            if not data:
                self.__logger.warning("Client %s disconnected before receiving authorization key", self.address())
                return False

            return self.__connection.authorization_key == data.decode("utf-8").strip()

        except Exception:
            self.__logger.exception("Exception during authorization for %s", self.address())

        return False

    async def __handle_packets(self) -> None:
        """Receives packet until client is no longer active.
        """

        parser = PacketParser()

        while self.is_active():
            try:
                data = await self.__connection.reader.read(1024)
            except Exception:
                self.__logger.exception("Exception during packet receiving")
                return

            if not data:
                self.__logger.info("Received no data from client %s", self.address())
                return

            packets = parser.feed(bytearray(data))

            for packet in packets:
                self.__received_packets.append(packet)
                on_tcp_receive.send(self, packet=packet)

            await asyncio.sleep(0)