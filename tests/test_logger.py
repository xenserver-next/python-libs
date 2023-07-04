# -*- coding: utf-8 -*-
"""Test xcp.logger.openLog()"""
import logging
import os
import sys
from pty import openpty
from time import tzset

# timemachine does not support 2.7:
from freezegun import freeze_time  # pyre-fixme[21] # cannot import it
from mock import mock_open, patch
from pyfakefs.fake_filesystem import FakeFileOpen

from xcp import logger

# In Python 3.x, bytes are a separate type and are shown using b'bytes':
expected_log = """\
INFO     [2023-06-27 08:00:00] Log message
INFO     [2023-06-27 08:00:00] Info message
DEBUG    [2023-06-27 08:00:00] b'Debug message'
ERROR    [2023-06-27 08:00:00] Error message
WARNING  [2023-06-27 08:00:00] Warning message
"""


@freeze_time("2023-06-27 08:00")
def test_log_to_file(caplog, fs):
    """Test xcp.logger.openLog() to work as expected"""
    os.environ["TZ"] = "UTC"  # get differing system time zones out of the way
    tzset()
    assert logger.openLog("critical.log") is True
    logger.critical("Critical message")
    logger.closeLogs()
    assert caplog.record_tuples == [("root", logging.CRITICAL, "Critical message")]
    with FakeFileOpen(fs)("critical.log") as logged:
        assert logged.read() == "CRITICAL [2023-06-27 08:00:00] Critical message\n"

    caplog.clear()
    assert logger.openLog("test.log", logging.DEBUG) is True
    # If pytest runs with --log-cli-level=INFO, ensure to have DEBUG logged on Python3:
    with caplog.at_level(logging.DEBUG, logger="root"):
        logger.log("Log message")
        logger.info("Info message")
        logger.debug(b"Debug message")
        logger.error("Error message")
        logger.warning("Warning message")
        logger.closeLogs()
        if logging.root.level == logging.DEBUG:  # Older pytest overrides this
            assert sorted(caplog.record_tuples) == [
                ("root", logging.DEBUG, "b'Debug message'"),
                ("root", logging.INFO, "Info message"),
                ("root", logging.INFO, "Log message"),
                ("root", logging.WARNING, "Warning message"),
                ("root", logging.ERROR, "Error message"),
            ]
            with FakeFileOpen(fs)("test.log") as logged:
                assert logged.read() == expected_log
    if sys.version_info >= (3, 0):  # With Python2.7, RotatingFileHandler only supports ASCII
        caplog.clear()
        assert logger.openLog("test-Unicode.log", logging.DEBUG) is True
        message = "✋➔Hello logger, this string has non-ASCII, Unicode characters! ✅"
        with caplog.at_level(logging.DEBUG, logger="root"):
            logger.log(message)
        logger.closeLogs()
        assert caplog.record_tuples == [("root", logging.INFO, message)]
        with FakeFileOpen(fs)("test-Unicode.log") as logged:
            assert logged.read() == "INFO     [2023-06-27 08:00:00] " + message + "\n"

        caplog.clear()
        assert logger.openLog("test-non-ASCII-bytes.log", logging.DEBUG) is True
        binarylog = b"Binary Log \xc2"
        with caplog.at_level(logging.DEBUG, logger="root"):
            logger.log(binarylog)
        logger.closeLogs()
        assert caplog.record_tuples == [("root", logging.INFO, "b'Binary Log \\xc2'")]
        with FakeFileOpen(fs)("test-non-ASCII-bytes.log") as logged:
            assert logged.read() == "INFO     [2023-06-27 08:00:00] b'Binary Log \\xc2'\n"


def test_openLog_mock_stdin():
    """Cover xcp.logger.openLog calling logging.StreamHandler(h) when h is a tty"""
    with patch("xcp.compat.open", mock_open()) as open_mock:
        master_fd, slave_fd = openpty()
        open_mock.return_value = os.fdopen(slave_fd)
        assert logger.openLog("test.log") is True
        os.close(slave_fd)
        os.close(master_fd)
        logger.closeLogs()
