import asyncio
import serial_asyncio_fast
import logging
from velbustcp.lib.packet.handlers.busstatus import BusStatus
from velbustcp.lib.settings.serial import SerialSettings
from velbustcp.lib.connection.serial.factory import set_serial_settings, find_port
from velbustcp.lib.connection.serial.serialprotocol import VelbusSerialProtocol
from velbustcp.lib.connection.serial.writerthread import WriterThread
from velbustcp.lib.signals import on_bus_receive, on_bus_fault


class Bus:
    def __init__(self, options: SerialSettings):
        """Initialises a bus connection."""
        self.__logger = logging.getLogger("__main__." + __name__)
        self.__options = options
        self.__bus_status: BusStatus = BusStatus()
        self.__do_reconnect: bool = False
        self.__connected: bool = False

        on_bus_receive.connect(self.handle_on_bus_receive)
        on_bus_fault.connect(self.handle_on_bus_fault)

    async def __reconnect(self):
        """Reconnects until active."""
        self.__logger.info("Attempting to connect")
        while self.__do_reconnect and not self.is_active():
            try:
                await self.__start()
            except Exception:
                self.__logger.exception("Couldn't create bus connection, waiting 5 seconds")
                await asyncio.sleep(5)

    def is_active(self) -> bool:
        """Returns whether or not the serial connection is active."""
        return self.__connected

    async def ensure(self):
        """Ensures that a connection with the bus is established."""
        if self.is_active() or self.__do_reconnect:
            return
        self.__do_reconnect = True
        await self.__reconnect()

    async def __start(self):
        """Starts up the serial communication if the serial connection is not yet active."""
        if self.is_active():
            return

        self.__port = find_port(options=self.__options)
        if not self.__port:
            raise ValueError("Couldn't find a port to open communication on")

        settings = set_serial_settings()
        self.__transport, self.__protocol = await serial_asyncio_fast.create_serial_connection(
            asyncio.get_event_loop(), VelbusSerialProtocol, url=self.__port, **settings
        )
        self.__connected = True

        self.__writer = WriterThread(self.__transport)
        self.__logger.info("Serial connection active on port %s", self.__port)

        await self.__writer.run()

    async def stop(self):
        """Stops the serial communication if the serial connection is active."""
        if not self.is_active():
            return

        self.__logger.info("Stopping serial connection")
        self.__do_reconnect = False
        self.__connected = False

        if self.__transport:
            self.__transport.close()

        if self.__writer:
            await self.__writer.close()

    async def send(self, packet: bytearray):
        """Queues a packet to be sent on the serial connection."""
        if self.is_active():
            await self.__writer.queue(packet)

    def handle_on_bus_receive(self, sender, **kwargs):
        old_state = self.__bus_status.alive
        packet = kwargs["packet"]
        self.__bus_status.receive_packet(packet)

        if old_state == self.__bus_status.alive:
            return

        if self.__bus_status.active:
            self.__writer.unlock()
        else:
            self.__writer.lock()

    async def on_reconnection(self):
        await self.stop()
        await self.ensure()

    def handle_on_bus_fault(self, sender, **kwargs):
        asyncio.create_task(self.on_reconnection())