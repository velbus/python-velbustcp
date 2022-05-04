import logging
from velbustcp.lib.connection.serial.bus import Bus
from velbustcp.lib.connection.tcp.networkmanager import NetworkManager
from velbustcp.lib.packet.handlers.busstatus import BusStatus
from velbustcp.lib.packet.packetcache import packet_cache
from velbustcp.lib.ntp.ntp import Ntp


class Bridge():
    """Bridge class for the Velbus-TCP connection.

    Connects serial and TCP connection(s) together.
    """

    def __init__(self, bus: Bus, network_manager: NetworkManager, ntp: Ntp):
        """Initialises the Bridge class.
        """

        # Logger
        self.__logger: logging.Logger = logging.getLogger("__main__." + __name__)

        # Create bus
        self.__bus: Bus = bus
        self.__bus.on_packet_received = self.__bus_packet_received
        self.__bus.on_packet_sent = self.__bus_packet_sent

        self.__bus_status: BusStatus = BusStatus()

        # Create network manager
        self.__network_manager: NetworkManager = network_manager
        self.__network_manager.on_packet_received = self.tcp_packet_received

        # Create NTP
        self.__ntp: Ntp = ntp
        self.__ntp.on_packet_send_request = self.send

    def start(self) -> None:
        """Starts bus and TCP network(s).
        """

        self.__bus.ensure()
        self.__network_manager.start()
        self.__ntp.start()

    def send(self, packet: bytearray) -> None:
        """Sends a packet that has been received internally (e.g. NTP).

        Args:
            packet (bytearray): The packet to be sent.
        """

        packet_id = packet_cache.add(packet)
        self.__bus.send(packet_id)

    def __bus_packet_received(self, packet_id: str) -> None:
        """Called when the serial connection receives a packet.

        Args:
            packet (bytearray): The received packet on the serial connection.
        """

        packet = packet_cache.get(packet_id)

        self.__logger.debug("[BUS IN] " + " ".join(hex(x) for x in packet))

        self.__bus_status.receive_packet(packet)

        if not self.__bus_status.alive:
            self.__bus.lock()
        else:
            self.__bus.unlock()

        self.__network_manager.send(packet_id)

    def __bus_packet_sent(self, packet_id: str) -> None:
        """Called when the bus has sent a packet.

        Args:
            packet_id (str): The id of the sent packet.
        """

        self.__network_manager.send(packet_id)

    def tcp_packet_received(self, packet_id: str):
        """Called when a network receives a packet from a client.

        Args:
            packet_id (str): The id of the packet.
        """

        packet = packet_cache.get(packet_id)
        self.__logger.debug("[TCP IN] " + " ".join(hex(x) for x in packet))

        if self.__bus.is_active():
            self.__bus.send(packet_id)

    def stop(self) -> None:
        """Stops NTP, bus and network.
        """

        self.__ntp.stop()
        self.__bus.stop()
        self.__network_manager.stop()
