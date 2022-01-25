import logging
from velbustcp.lib import consts


class BusStatus():

    __active: bool = False
    __buffer_ready: bool = False

    def __init__(self):
        self.__logger = logging.getLogger(__name__)

    @property
    def alive(self):
        return self.__active and self.__buffer_ready

    @property
    def active(self):
        return self.__active

    @property
    def buffer_ready(self):
        return self.__buffer_ready

    def receive_packet(self, packet: bytearray) -> None:

        # Buffer full/off?
        has_command = (packet[3] and 0x0F) != 0
        high_prio = packet[1] == consts.PRIORITY_HIGH

        if has_command and high_prio:
            command = packet[4]

            if command == consts.COMMAND_BUS_ACTIVE:
                self.__logger.info("Received bus active")
                self.__active = True

            elif command == consts.COMMAND_BUS_OFF:
                self.__logger.info("Received bus off")
                self.__active = False

            elif command == consts.COMMAND_BUS_BUFFERREADY:
                self.__logger.info("Received bus buffer ready")
                self.__buffer_ready = True

            elif command == consts.COMMAND_BUS_BUFFERFULL:
                self.__logger.info("Received bus buffer full")
                self.__buffer_ready = False
