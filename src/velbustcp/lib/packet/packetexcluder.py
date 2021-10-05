from velbustcp.lib.connection.client import Client


def should_accept(packet: bytearray, client: Client) -> bool:
    """Determines whether or not given packet should be accepted from given client.

    Args:
        packet (bytearray): A Velbus packet.
        client (Client): A TCP Client.

    Returns:
        bool: A boolean, indicating whether or not the packet should be accepted from the client.
    """

    return True
