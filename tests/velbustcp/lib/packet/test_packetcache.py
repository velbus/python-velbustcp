import pytest

from velbustcp.lib.packet.packetcache import PacketCache


def test_cache_add():
    cache = PacketCache()

    data = bytearray([0x00])
    id = cache.add(data)

    assert id


def test_cache_retrieve():
    cache = PacketCache()

    data = bytearray([0x00])
    id = cache.add(data)

    assert data == cache.get(id)


def test_cache_remove():
    cache = PacketCache()

    data = bytearray([0x00])
    id = cache.add(data)
    cache.delete(id)

    with pytest.raises(KeyError):
        cache.get(id)
