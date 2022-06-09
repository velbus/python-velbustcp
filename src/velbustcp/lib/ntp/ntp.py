import sys

if sys.version_info >= (3, 8):
    from typing import Protocol
else:  # pragma: no cover
    from typing_extensions import Protocol

from pytz import utc
from tzlocal import get_localzone
from datetime import datetime, timedelta
import threading
import time
import logging

from velbustcp.lib.packet.packetparser import PacketParser
from velbustcp.lib.settings.ntp import NtpSettings


class OnPacketSendRequest(Protocol):
    def __call__(self, packet: bytearray) -> None:
        pass


class Ntp():

    on_packet_send_request: OnPacketSendRequest

    def __init__(self, options: NtpSettings):
        """Initialises the NTP class.
        """

        self.__logger = logging.getLogger("__main__." + __name__)

        self.__options = options
        self.__is_active = False
        self.__sleep_event = threading.Event()
        self.__settings = options
        self.__timezone = get_localzone()

    def start(self) -> None:
        """Periodically broadcasts the time on the bus.
        """

        if self.__options.enabled and not self.is_active():
            self.__thread = threading.Thread(target=self.__do_ntp)
            self.__thread.start()

    def is_active(self) -> bool:
        """Returns whether or not NTP is active.

        Returns:
            bool: Whether or not NTP is active.
        """

        return self.__is_active

    def stop(self) -> None:
        """Stops the NTP broadcasting.
        """

        self.__is_active = False
        self.__sleep_event.set()

    def __do_ntp(self) -> None:
        """Sleep thread which will send the NTP packets once every hour, and once at start.
        """

        self.__logger.info("Started NTP broadcast, will wait until next minute transition")

        self.__is_active = True

        while True and self.is_active():

            # Send the NTP packets on next minute transition
            self.__send_next_transition()

            if not self.is_active():
                break

            # Figure out how long to sleep:
            # Till next hour transition (if no synctime specified)
            # Till synctime
            # Till next DST transition

            now = utc.localize(datetime.utcnow()).astimezone(self.__timezone)

            # DST - if the timezone has it
            until_dst = None
            if hasattr(self.__timezone, '_utc_transition_times'):
                until_dst = next(time for time in self.__timezone._utc_transition_times if time > datetime.utcnow())
                until_dst = utc.localize(until_dst).astimezone(self.__timezone)            
            
            # No synctime: one hour
            if not self.__settings.synctime:
                until_synctime = now + timedelta(hours=1) - timedelta(minutes=now.minute, seconds=now.second, microseconds=now.microsecond)

                if not until_dst or until_synctime < until_dst:
                    until = until_synctime
                else:
                    until = until_dst

            # Synctime set, check between timesync and DST which is closest
            else:

                # Timesync
                splitted = self.__settings.synctime.split(":")
                hh = int(splitted[0])
                mm = int(splitted[1])

                until_timesync = utc.localize(datetime.utcnow()).astimezone(self.__timezone).replace(hour=hh, minute=mm, second=0, microsecond=0)

                # Add one day if it has already passed
                if until_timesync < now:
                    until_timesync = until_timesync + timedelta(days=1)

                if until_timesync < until_dst:
                    until = until_timesync
                else:
                    until = until_dst

            self.__logger.info("Waiting for next NTP broadcast at {0}".format(until))

            # Sleep until a minute before
            until = until - timedelta(minutes=1)
            dt = until - now
            self.__sleep_event.wait(dt.total_seconds())

    def __send_next_transition(self) -> None:
        """Sends a time packet on the bus on next minute transition.
        """

        # Go to the next minute
        now = datetime.utcnow()
        until = now + timedelta(minutes=1) - timedelta(seconds=now.second, microseconds=now.microsecond)

        # Wait until we passed the 'until' time
        while (datetime.utcnow() < until) and self.is_active():
            time.sleep(0.1)

        # Now that we're at the minute transition, send the packet
        if self.is_active():

            # Get current time
            # Don't use the until var, as this will not have the DST calculated in on DST transition.
            timezoned = utc.localize(datetime.utcnow()).astimezone(self.__timezone)

            # Create the packets to send, based on the until time
            time_packet = self.get_time_packet(timezoned)
            date_packet = self.get_date_packet(timezoned)
            dst_packet = self.get_dst_packet()

            self.__logger.info("Broadcasting NTP {0}".format(timezoned))

            if self.on_packet_send_request:
                self.on_packet_send_request(time_packet)
                self.on_packet_send_request(date_packet)
                self.on_packet_send_request(dst_packet)

    def get_time_packet(self, dt: datetime) -> bytearray:
        """Prepares a time packet according to passed datetime.

        Args:
            dt (datetime): The datetime to create a packet for.
        Returns:
            bytearray: A Velbus packet containing the time.
        """

        packet = bytearray()
        packet.append(0x0F)
        packet.append(0xFB)
        packet.append(0x00)
        packet.append(0x04)
        packet.append(0xD8)
        packet.append(dt.weekday())
        packet.append(dt.hour)
        packet.append(dt.minute)
        packet.append(PacketParser.checksum(packet))
        packet.append(0x04)

        return packet

    def get_date_packet(self, dt: datetime) -> bytearray:
        """Prepares a date packet according to passed datetime.

        Args:
            dt (datetime): The datetime to create a packet for.
        Returns:
            bytearray: A Velbus packet containing the date.
        """

        year_bytes = dt.year.to_bytes(2, "big")

        packet = bytearray()
        packet.append(0x0F)
        packet.append(0xFB)
        packet.append(0x00)
        packet.append(0x05)
        packet.append(0xB7)
        packet.append(dt.day)
        packet.append(dt.month)
        packet.append(year_bytes[0])
        packet.append(year_bytes[1])
        packet.append(PacketParser.checksum(packet))
        packet.append(0x04)

        return packet

    def get_dst_packet(self) -> bytearray:
        """Prepares a DST Velbus packet.

        Returns:
            bytearray: A Velbus packet containing the DST.
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
