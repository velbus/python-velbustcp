from velbustcp.lib.connection.client import Client

def should_accept(packet, client):

    assert isinstance(packet, bytearray)
    assert isinstance(client, Client)

    return True