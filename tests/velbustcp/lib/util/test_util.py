import logging
import logging.handlers

from velbustcp.lib.settings.logging import LoggingSettings
from velbustcp.lib.util.util import setup_logging, str2bool


def test_str2bool():
    assert str2bool("true")
    assert str2bool("yes")
    assert str2bool("y")
    assert str2bool("t")
    assert str2bool("1")


def test_defaults():

    settings = LoggingSettings()
    logger = setup_logging(settings)

    assert logger.name == settings.name
    assert logger.level == logging.INFO
    assert isinstance(logger.handlers[0], logging.StreamHandler)


def test_type_debug():

    settings = LoggingSettings()
    settings.name = "test-logger-debug"
    settings.type = "debug"

    logger = setup_logging(settings)
    assert logger.name == settings.name
    assert logger.level == logging.DEBUG


def test_output_syslog():

    settings = LoggingSettings()
    settings.name = "test-logger-syslog"
    settings.output = "syslog"

    logger = setup_logging(settings)
    assert logger.name == settings.name
    assert isinstance(logger.handlers[0], logging.handlers.SysLogHandler)
