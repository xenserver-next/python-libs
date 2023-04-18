import sys
import unittest
from mock import patch, Mock, DEFAULT

from xcp.cmd import OutputCache

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
        mock_popen_stdout = expected_stdout = "line1\nline2\n"
        mock_popen_stderr = expected_stderr = "mock error"
        # Python3 Popen().communicate() returns a tuple of bytes:
        if sys.version_info.major != 2:
            mock_popen_stdout = expected_stdout.encode()
            mock_popen_stderr = expected_stderr.encode()

        with patch("xcp.cmd.subprocess.Popen") as popen_mock:
            # mock Popen .communicate and .returncode for
            # `mock_popen_stdout`on stdout, `mock_popen_stderr` on stderr, and an exit
            # value of 42
            communicate_mock = Mock(return_value=(mock_popen_stdout, mock_popen_stderr))
            popen_mock.return_value.communicate = communicate_mock
            def communicate_side_effect(_input_text):
                popen_mock.return_value.returncode = 42
                return DEFAULT
            communicate_mock.side_effect = communicate_side_effect

            # uncached runCmd
            data = self.c.runCmd(['ls', '/tmp'], True)
            popen_mock.assert_called_once()
            self.assertEqual(data, (42, expected_stdout))

            # rerun as cached
            popen_mock.reset_mock()
            data = self.c.runCmd(['ls', '/tmp'], with_stdout=True, with_stderr=True)
            popen_mock.assert_not_called()
            self.assertEqual(data, (42, expected_stdout, expected_stderr))
