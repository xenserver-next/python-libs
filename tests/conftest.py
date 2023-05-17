# conftest.py
"""
Pytest auto configuration.

This module is run automatically by pytest to define and enable fixtures.
"""

# pyre does not find the pytest module when run by tox -e py311-pyre
# pyre-ignore-all-errors[21]
import subprocess
import warnings

import pytest

# subprocess.Popen() can only be wrapped for all test cases, not individually:
class PopenWrapper(subprocess.Popen):
    """Global wrapper of subprocess.Popen() for pytest tests in this directory"""
    def __init__(self, *args, **kwargs):
        """Wrap Popen, replacing /sbin/biosdevname with tests/data/biosdevname"""
        # Redirect for tests/test_biosdevname.py: /sbin/biosdevname -> tests/data/biosdevname:
        if args[0][0] == "/sbin/biosdevname":
            args[0][0] = "tests/data/biosdevname"
        super(subprocess.Popen, self).__init__(*args, **kwargs)

subprocess.Popen = PopenWrapper  # type: ignore[misc]
"""Wraps subprocess.Popen for test cases which would like to redirect Popen commands"""

@pytest.fixture(autouse=True)
def set_warnings():
    """
    Enable the default warning filter. It enables showing these warnings:
    - DeprecationWarning
    - ImportWarning
    - PendingDeprecationWarning
    - ResourceWarning

    The ResourceWarning helps to catch e.g. unclosed files:
    https://docs.python.org/3/library/devmode.html#resourcewarning-example

    One purpose of this fixture that with it, we can globally enable
    Development Mode (https://docs.python.org/3/library/devmode.html)
    using setenv = PYTHONDEVMODE=yes in tox.int which enables further
    run-time checking during tests.

    By additionally using setenv = PYTHONWARNINGS=ignore in tox.ini,
    we can disabling the Deprecation warnings wihch pytest plugins exhibit
    (which we are not interested in, those are not our responsiblity).
    and this fixture will still enable the default warning filter to
    have e.g. ResourceWarning checks enabled.

    Another nice effect is that also during interactive pytest use, the
    default warning filter also provides checking of ResourceWarning:
    """
    warnings.simplefilter("default")
