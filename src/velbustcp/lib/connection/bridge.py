from velbustcp.lib.connection.serial.bus import Bus
from velbustcp.lib.connection.tcp.networkmanager import NetworkManager
from velbustcp.lib.signals import on_bus_receive, on_bus_send, on_tcp_receive
import asyncio


class Bridge():
    """Bridge class for the Velbus-TCP connection.

    Connects serial and TCP connection(s) together.
    """

    __bus: Bus
    __network_manager: NetworkManager

    def __init__(self, bus: Bus, network_manager: NetworkManager):
        """Initialises the Bridge class.
        """

        def handle_bus_receive(sender, **kwargs):
            packet = kwargs["packet"]
            asyncio.create_task(self.__network_manager.send(packet))
        self.handle_bus_receive = handle_bus_receive
        on_bus_receive.connect(handle_bus_receive)

        def handle_bus_send(sender, **kwargs):
            packet = kwargs["packet"]
            asyncio.create_task(self.__network_manager.send(packet))
        self.handle_bus_send = handle_bus_send
        on_bus_send.connect(handle_bus_send)

        def handle_tcp_receive(sender, **kwargs):
            packet = kwargs["packet"]
            asyncio.create_task(self.__bus.send(packet))
        self.handle_tcp_receive = handle_tcp_receive
        on_tcp_receive.connect(handle_tcp_receive)

        self.__bus: Bus = bus
        self.__network_manager: NetworkManager = network_manager

    async def start(self) -> None:
        """Starts bus and TCP network(s).
        """

        serial_task = asyncio.create_task(self.__bus.ensure())
        tcp_task = asyncio.create_task(self.__network_manager.start())

        await asyncio.gather(serial_task, tcp_task)

    async def stop(self) -> None:
        """Stops NTP, bus and network.
        """

        await self.__network_manager.stop()
        await self.__bus.stop()
