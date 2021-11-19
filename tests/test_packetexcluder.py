import pytest
from velbustcp.lib.packet.packetexcluder import should_accept


def test_should_accept():
    assert True == should_accept(None, None)