# Copyright (c) 2013, Citrix Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Command processing"""

import subprocess
import sys

from xcp import logger
from xcp.compat import open_defaults_for_utf8_text

def _encode_command_to_bytes(command):
    # When the locale not an UTF-8 locale, Python3.6 Popen can't deal with ord() >= 128
    # when the command contains strings, not bytes. Therefore, convert any strings to bytes:
    if sys.version_info >= (3, 0):
        if isinstance(command, str):
            command = command.encode()
        elif isinstance(command, list):
            for idx, arg in enumerate(command):
                if isinstance(arg, str):
                    command[idx] = arg.encode()
    return command

def runCmd(command, with_stdout=False, with_stderr=False, inputtext=None, **kwargs):
    # sourcery skip: assign-if-exp, hoist-repeated-if-condition, reintroduce-else

    if inputtext is not None:
        kwargs["mode"] = "t" if isinstance(inputtext, str) else "b"
    if with_stdout or with_stderr:
        open_defaults_for_utf8_text(None, kwargs)
    kwargs.pop("mode", "")

    command = _encode_command_to_bytes(command)

    # bufsize=1 means buffered in 2.7, but means line buffered in Py3 (not valid in binary mode)
    # bufsize=-1 is the equivalent of bufsize=1 in Python >= 3.3.1

    # pylint: disable-next=unexpected-keyword-arg
    cmd = subprocess.Popen(command, bufsize=(1 if sys.version_info < (3, 3) else -1),
                           stdin=(inputtext and subprocess.PIPE or None),
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           shell=not isinstance(command, list),
                           **kwargs)
    (out, err) = cmd.communicate(inputtext)
    rv = cmd.returncode

    l = "ran %s; rc %d" % (str(command), rv)
    if inputtext and isinstance(inputtext, str):
        l += " with input %s" % inputtext
    if out != "" and isinstance(out, str):
        l += "\nSTANDARD OUT:\n" + out
    if err != "" and isinstance(err, str):
        l += "\nSTANDARD ERROR:\n" + err

    for line in l.split('\n'):
        logger.debug(line)

    if with_stdout and with_stderr:
        return rv, out, err
    if with_stdout:
        return rv, out
    if with_stderr:
        return rv, err
    return rv

class OutputCache(object):
    def __init__(self):
        self.cache = {}

    def fileContents(self, fn, *args, **kwargs):
        mode, other_kwargs = open_defaults_for_utf8_text(args, kwargs)
        key = "file:" + fn + "," + mode + (str(other_kwargs) if other_kwargs else "")
        if key not in self.cache:
            logger.debug("Opening " + key)
            # pylint: disable=unspecified-encoding
            with open(fn, *args, **kwargs) as f:
                self.cache[key] = f.read() if "b" in mode else "".join(f.readlines())
        return self.cache[key]

    def runCmd(self, command, with_stdout=False, with_stderr=False, inputtext=None, **kwargs):
        key = str(command) + str(kwargs.get("mode")) + str(inputtext)
        rckey = 'cmd.rc:' + key
        outkey = 'cmd.out:' + key
        errkey = 'cmd.err:' + key
        if rckey not in self.cache:
            self.cache[rckey], self.cache[outkey], self.cache[errkey] = runCmd(  # pyright: ignore
                command, True, True, inputtext, **kwargs
            )
        if with_stdout and with_stderr:
            return self.cache[rckey], self.cache[outkey], self.cache[errkey]
        elif with_stdout:
            return self.cache[rckey], self.cache[outkey]
        elif with_stderr:
            return self.cache[rckey], self.cache[errkey]
        return self.cache[rckey]

    def clearCache(self):
        self.cache.clear()
