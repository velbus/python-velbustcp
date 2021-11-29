from velbustcp.lib.packet.packetexcluder import should_accept


def test_should_accept():
    assert should_accept(None, None)
