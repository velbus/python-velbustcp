import argparse
import json
import sys
import asyncio

from velbustcp.lib.connection.bridge import Bridge
from velbustcp.lib.connection.serial.bus import Bus
from velbustcp.lib.connection.tcp.network import Network
from velbustcp.lib.connection.tcp.networkmanager import NetworkManager
from velbustcp.lib.settings.settings import validate_and_set_settings
from velbustcp.lib.util.util import setup_logging


class Main():
    """Main class for the Velbus-TCP connection.

    Connects serial and TCP connection together.
    """

    def __init__(self):
        """Initialises the main class.
        """

        # Bridge
        from velbustcp.lib.settings.settings import serial_settings
        bus = Bus(options=serial_settings)

        # Network manager
        network_manager = NetworkManager()
        from velbustcp.lib.settings.settings import network_settings
        for connection in network_settings:
            network = Network(options=connection)
            network_manager.add_network(network)

        self.__bridge = Bridge(bus, network_manager)

    async def start(self):
        """Starts the bridge."""
        await self.__bridge.start()

    async def stop(self):
        """Stops the bridge."""
        await self.__bridge.stop()


async def main_async(args=None):
    """Main asynchronous method."""
    parser = argparse.ArgumentParser(description="Velbus communication")
    parser.add_argument("--settings", help="Settings file", required=False)
    args = parser.parse_args()

    # If settings are supplied, read and validate them
    if args.settings:
        # Open settings file
        with open(args.settings, 'r') as f:
            settings = json.load(f)

        validate_and_set_settings(settings)

    # Setup logging
    from velbustcp.lib.settings.settings import logging_settings
    logger = setup_logging(logging_settings)

    # Create main class
    main = Main()

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(await main.start())
        loop.run_forever()

    except KeyboardInterrupt:
        logger.info("Interrupted, shutting down")

    except Exception as e:
        logger.exception(e)

    finally:
        await main.stop()

    logger.info("Shutdown")


# entrypoint for the snap
def main(args=None):
    """Main method."""
    asyncio.run(main_async(args))


if __name__ == '__main__':
    sys.exit(main())
