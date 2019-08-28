from datetime import datetime, timedelta
from .packetparser import PacketParser
import threading
import time
import logging

class Ntp():

    def __init__(self, sendcb):
        self.__is_active = False
        self.__sleep_event = threading.Event()
        self.__sendcb = sendcb
        self.__logger = logging.getLogger("VelbusTCP")

    def start(self):
        """
        Periodically broadcasts the time on the bus.
        """

        self.__thread = threading.Thread(target=self.__do_ntp)
        self.__thread.start()

    def is_active(self):
        return self.__is_active

    def stop(self):
        self.__is_active = False
        self.__sleep_event.set()

    def __do_ntp(self):
        """
        Sleep thread which will send the NTP packets once every hour, and once at start.
        """

        self.__logger.info("Started NTP broadcast, will wait until next minute transition")

        self.__is_active = True

        while True and self.is_active():
            
            # Send the NTP packets on next minute transition
            self.__send_next_transition()

            # Sleep until a minute before next hour passing
            now = datetime.now()
            until = now + timedelta(hours=1) - timedelta(minutes=now.minute + 1, seconds=now.second, microseconds=now.microsecond)

            dt = until-now
            self.__sleep_event.wait(dt.total_seconds())

    def __send_next_transition(self):
        """
        Sends an time packet on the bus on next minute transition.
        """

        # Go to the next minute
        now = datetime.now()
        until = now + timedelta(minutes=1) - timedelta(seconds=now.second, microseconds=now.microsecond)

        # Create the packets to send, based on the until time
        time_packet = self.get_time_packet(until)
        date_packet = self.get_date_packet(until)
        dst_packet = self.get_dst_packet()

        # Wait until we passed the 'until' time
        while (datetime.now() < until) and self.is_active():
            time.sleep(0.1)
        
        if self.is_active():
            self.__logger.info("Broadcasting NTP {0}".format(until))
            self.__sendcb(time_packet)
            self.__sendcb(date_packet)
            self.__sendcb(dst_packet)

    def get_time_packet(self, time):
        """
        Prepares a time packet according to passed datetime
        """

        assert isinstance(time, datetime)

        packet = bytearray()
        packet.append(0x0F)
        packet.append(0xFB)
        packet.append(0x00)
        packet.append(0x04)
        packet.append(0xD8)
        packet.append(time.weekday())
        packet.append(time.hour)
        packet.append(time.minute)
        packet.append(PacketParser.checksum(packet))
        packet.append(0x04)

        return packet

    def get_date_packet(self, time):
        """
        Prepares a date packet according to passed datetime
        """

        assert isinstance(time, datetime)

        packet = bytearray()
        packet.append(0x0F)
        packet.append(0xFB)
        packet.append(0x00)
        packet.append(0x05)
        packet.append(0xB7)
        packet.append(time.day)
        packet.append(time.month)
        packet.append((time.year and 0xFF00) >> 8) 
        packet.append(time.year and 0xFF)
        packet.append(PacketParser.checksum(packet))
        packet.append(0x04)

        return packet

    def get_dst_packet(self):
        """
        Prepares a dst packet
        """

        packet = bytearray()
        packet.append(0x0F)
        packet.append(0xFB)
        packet.append(0x00)
        packet.append(0x02)
        packet.append(0xAF)
        packet.append(0x00)
        packet.append(PacketParser.checksum(packet))
        packet.append(0x04)

        return packet