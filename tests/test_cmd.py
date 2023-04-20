import subprocess
import unittest
from mock import patch, Mock, DEFAULT

from xcp import xcp_popen_text_kwargs
from xcp.cmd import OutputCache

from .xcptestlib import set_c_locale

set_c_locale()

class TestCache(unittest.TestCase):
    def setUp(self):
        self.c = OutputCache()

    def test_fileContents(self):
        with patch("xcp.cmd.open") as open_mock:
            open_mock.return_value.readlines = Mock(return_value=["line1\n", "line2\n"])

            # uncached fileContents
            data = self.c.fileContents('/tmp/foo')
            open_mock.assert_called_once_with("/tmp/foo")
            self.assertEqual(data, "line1\nline2\n")

            # rerun as cached
            open_mock.reset_mock()
            data = self.c.fileContents('/tmp/foo')
            open_mock.assert_not_called()
            self.assertEqual(data, "line1\nline2\n")

            # rerun after clearing cache
            open_mock.reset_mock()
            self.c.clearCache()
            data = self.c.fileContents('/tmp/foo')
            open_mock.assert_called_once_with("/tmp/foo")
            self.assertEqual(data, "line1\nline2\n")

    def test_runCmd(self):
        output_data = "output with\nUTF-8:\u25b6\U0001f601\n"
        stderr_data = "error with\nUTF-8:\u2614\U0001f629\n"

        with patch("xcp.cmd.subprocess.Popen") as popen_mock:
            # mock Popen .communicate and .returncode for
            # `output_data` on stdout, `stderr_data` on stderr, and an exit
            # value of 42
            communicate_mock = Mock(return_value=(output_data, stderr_data))
            popen_mock.return_value.communicate = communicate_mock
            def communicate_side_effect(_input_text):
                popen_mock.return_value.returncode = 42
                return DEFAULT
            communicate_mock.side_effect = communicate_side_effect

            # uncached runCmd
            data = self.c.runCmd(['ls', '/tmp'], True)
            popen_mock.assert_called_once_with(["ls", "/tmp"],
                                               bufsize=1,
                                               stdin=None,
                                               stdout=subprocess.PIPE,
                                               stderr=subprocess.PIPE,
                                               shell=False,
                                               **xcp_popen_text_kwargs)
            self.assertEqual(data, (42, output_data))

            # rerun as cached
            popen_mock.reset_mock()
            data = self.c.runCmd(['ls', '/tmp'], with_stdout=True, with_stderr=True)
            popen_mock.assert_not_called()
            self.assertEqual(data, (42, output_data, stderr_data))

    def test_runCmdCatStdin(self):
        """Call cat with a given UTF-8 input text and expect it to be returned"""
        stdin = "output with\nUTF-8:\u25b6\U0001f601"
        ret = self.c.runCmd("cat", inputtext=stdin, with_stdout=True, with_stderr=True)
        self.assertEqual(ret, (0, stdin, ""))
