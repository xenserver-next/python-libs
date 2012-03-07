#!/usr/bin/env python

import unittest, sys, os, os.path as path, logging
from copy import deepcopy

try:
    import cStringIO as StringIO
except ImportError:
    import StringIO

try:
    import xcp
except ImportError:
    print >>sys.stderr, "Must run with run-test.sh to bind mount 'xcp'"


from xcp.net.ifrename.static import StaticRules
from xcp.net.ifrename.macpci import MACPCI
from xcp.logger import LOG, openLog, closeLogs


class TestLoadAndParse(unittest.TestCase):

    def setUp(self):
        self.logbuf = StringIO.StringIO()
        openLog(self.logbuf, logging.NOTSET)

    def tearDown(self):

        closeLogs()
        self.logbuf.close()

    def test_null(self):
        sr = StaticRules()

        self.assertEqual(sr.path, None)
        self.assertEqual(sr.fd, None)
        self.assertEqual(sr.formulae, {})
        self.assertEqual(sr.rules, [])

        self.assertFalse(sr.load_and_parse())
        self.assertEqual(sr.formulae, {})
        self.assertEqual(sr.rules, [])

    def test_empty(self):

        fd = StringIO.StringIO("")
        sr = StaticRules(fd = fd)

        self.assertTrue(sr.load_and_parse())
        self.assertEqual(sr.formulae, {})
        self.assertEqual(sr.rules, [])

    def test_comment(self):

        fd = StringIO.StringIO("#comment")
        sr = StaticRules(fd = fd)

        self.assertTrue(sr.load_and_parse())
        self.assertEqual(sr.formulae, {})
        self.assertEqual(sr.rules, [])

    def test_comment_and_empty(self):

        fd = StringIO.StringIO("\n # Another Comment\n ")
        sr = StaticRules(fd = fd)

        self.assertTrue(sr.load_and_parse())
        self.assertEqual(sr.formulae, {})
        self.assertEqual(sr.rules, [])

    def test_single_incorrect_mac(self):

        fd = StringIO.StringIO('eth0:mac="foo"')
        sr = StaticRules(fd = fd)

        self.assertTrue(sr.load_and_parse())
        self.assertEqual(sr.formulae, {})
        self.assertEqual(sr.rules, [])

    def test_single_mac(self):

        fd = StringIO.StringIO('eth0:mac="AB:CD:EF:AB:CD:EF"')
        sr = StaticRules(fd = fd)

        self.assertTrue(sr.load_and_parse())
        self.assertEqual(sr.formulae, {'eth0': ('mac', 'AB:CD:EF:AB:CD:EF')})
        self.assertEqual(sr.rules, [])

    def test_single_invalid_pci(self):

        fd = StringIO.StringIO('eth0:pci="bar"')
        sr = StaticRules(fd = fd)

        self.assertTrue(sr.load_and_parse())
        self.assertEqual(sr.formulae, {})
        self.assertEqual(sr.rules, [])

    def test_single_pci(self):

        fd = StringIO.StringIO('eth0:pci="0000:00:00.1"')
        sr = StaticRules(fd = fd)

        self.assertTrue(sr.load_and_parse())
        self.assertEqual(sr.formulae, {"eth0": ("pci", "0000:00:00.1")})
        self.assertEqual(sr.rules, [])

    def test_single_invalid_ppn(self):

        fd = StringIO.StringIO('eth0:ppn="baz"')
        sr = StaticRules(fd = fd)

        self.assertTrue(sr.load_and_parse())
        self.assertEqual(sr.formulae, {})
        self.assertEqual(sr.rules, [])

    def test_single_ppn(self):

        fd = StringIO.StringIO('eth0:ppn="pci2p3"')
        sr = StaticRules(fd = fd)

        self.assertTrue(sr.load_and_parse())
        self.assertEqual(sr.formulae, {"eth0": ("ppn", "pci2p3")})
        self.assertEqual(sr.rules, [])

    def test_single_label(self):

        fd = StringIO.StringIO('eth0:label="somestring"')
        sr = StaticRules(fd = fd)

        self.assertTrue(sr.load_and_parse())
        self.assertEqual(sr.formulae, {"eth0": ("label", "somestring")})
        self.assertEqual(sr.rules, [])


class TestGenerate(unittest.TestCase):

    def setUp(self):
        self.logbuf = StringIO.StringIO()
        openLog(self.logbuf, logging.NOTSET)

        self.state = [
            MACPCI("01:23:45:67:89:0a", "0000:00:01.0", kname="side-11-eth2",
                   ppn="pci2p1", label="Ethernet1"),
            MACPCI("03:23:45:67:89:0a", "0000:00:10.0", kname="side-12-eth34",
                   ppn="pci2p1", label=""),
            MACPCI("04:23:45:67:89:0a", "0000:00:10.1", kname="side-123-eth23",
                   ppn="pci2p2", label="")
            ]

    def tearDown(self):

        closeLogs()
        self.logbuf.close()

    def test_null(self):

        fd = StringIO.StringIO('eth0:label="somestring"')
        sr = StaticRules(fd = fd)
        self.assertTrue(sr.load_and_parse())
        sr.generate([])

        self.assertEqual(sr.rules, [])

    def test_single_not_matching_state(self):

        fd = StringIO.StringIO('eth0:label="somestring"')
        sr = StaticRules(fd = fd)
        self.assertTrue(sr.load_and_parse())
        sr.generate(self.state)

        self.assertEqual(sr.rules, [])

    def test_single_mac_matching(self):

        fd = StringIO.StringIO('eth0:mac="01:23:45:67:89:0a"')
        sr = StaticRules(fd = fd)
        self.assertTrue(sr.load_and_parse())

        sr.generate(self.state)

        self.assertEqual(sr.rules,[
                MACPCI("01:23:45:67:89:0a", "0000:00:01.0", tname="eth0")
                ])

    def test_single_pci_matching(self):

        fd = StringIO.StringIO('eth0:pci="0000:00:10.0"')
        sr = StaticRules(fd = fd)
        self.assertTrue(sr.load_and_parse())

        sr.generate(self.state)

        self.assertEqual(sr.rules,[
                MACPCI("03:23:45:67:89:0a", "0000:00:10.0", tname="eth0")
                ])

    def test_single_ppn_matching(self):

        fd = StringIO.StringIO('eth0:ppn="pci2p2"')
        sr = StaticRules(fd = fd)
        self.assertTrue(sr.load_and_parse())

        sr.generate(self.state)

        self.assertEqual(sr.rules,[
                MACPCI("04:23:45:67:89:0a", "0000:00:10.1", tname="eth0")
                ])

    def test_single_label_matching(self):

        fd = StringIO.StringIO('eth0:label="Ethernet1"')
        sr = StaticRules(fd = fd)
        self.assertTrue(sr.load_and_parse())

        sr.generate(self.state)

        self.assertEqual(sr.rules,[
                MACPCI("01:23:45:67:89:0a", "0000:00:01.0", tname="eth0")
                ])


class TestSave(unittest.TestCase):

    def setUp(self):
        self.logbuf = StringIO.StringIO()
        openLog(self.logbuf, logging.NOTSET)

    def tearDown(self):

        closeLogs()
        self.logbuf.close()

    def test_empty(self):

        sr = StaticRules()
        self.assertEqual(sr.write(False), "")

    def test_one_valid(self):

        sr = StaticRules()
        sr.formulae = {"eth0": ("ppn", "pci1p1"),
                       }

        desired_result = "eth0:ppn=\"pci1p1\"\n"

        self.assertEqual(sr.write(False), desired_result)

    def test_one_invalid_method(self):

        sr = StaticRules()
        sr.formulae = {"eth0": ("ppf", "foobaz"),
                       }

        self.assertEqual(sr.write(False), "")


    def test_two_valid(self):

        sr = StaticRules()
        sr.formulae = {"eth0": ("ppn", "pci1p1"),
                       "eth1": ("label", "Ethernet1"),
                       }

        desired_result = (
            "eth0:ppn=\"pci1p1\"\n"
            "eth1:label=\"Ethernet1\"\n"
            )

        self.assertEqual(sr.write(False), desired_result)


if __name__ == "__main__":
    unittest.main()