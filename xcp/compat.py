"""Helper module for setting up binary or UTF-8 I/O for Popen and open in Python 3.6 and newer"""
import sys

if sys.version_info >= (3, 0):
    open_utf8 = {"encoding": "utf-8", "errors": "replace"}
else:
    open_utf8 = {}


def open_defaults_for_utf8_text(args, kwargs):
    """Setup keyword arguments for UTF-8 text mode with codec error handler to replace chars"""

    mode = kwargs.get("mode", "")
    if args:
        mode = args[0]
    if not mode or not isinstance(mode, str):
        raise ValueError("The mode argument is required! r|t for text, b for binary")
    if sys.version_info >= (3, 0) and "b" not in mode:
        kwargs.setdefault("encoding", "utf-8")
        kwargs.setdefault("errors", "replace")
    return mode
