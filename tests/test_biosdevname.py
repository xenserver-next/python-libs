import unittest
from mock import patch, Mock

from xcp.net.biosdevname import has_ppn_quirks, all_devices_all_names

class TestQuirks(unittest.TestCase):

    def test_ppn_none(self):
        self.assertFalse(has_ppn_quirks([]))

    def test_ppn_empty(self):
        self.assertFalse(has_ppn_quirks([{},{},{}]))

    def test_ppn_false(self):
        self.assertFalse(has_ppn_quirks(
                [{"SMBIOS Instance": 1},
                 {"SMBIOS Instance": 2},
                 {"SMBIOS Instance": 3}
                 ]))

    def test_ppn_true(self):
        self.assertTrue(has_ppn_quirks(
                [{"SMBIOS Instance": 1},
                 {"SMBIOS Instance": 1}
                 ]))

class TestDeviceNames(unittest.TestCase):
    expected_devices = {
        "eth0": {
            "BIOS device": {"physical": "em1", "all_ethN": "eth0"},
            "Kernel name": "eth0",
            "Permanent MAC": "EC:F4:BB:C3:AF:A8",
            "Assigned MAC": "EC:F4:BB:C3:AF:A8",
            "Driver": "ixgbe",
            "Driver version": "5.9.4",
            "Firmware version": "0x8000095c, 19.5.12",
            "Bus Info": "0000:01:00.0",
            "PCI name": "0000:01:00.0",
            "PCI Slot": "embedded",
            "SMBIOS Device Type": "Ethernet",
            "SMBIOS Instance": "1",
            "SMBIOS Label": "Integrated NIC 1",
            "sysfs Label": "NIC1",
            "Embedded Index": "1",
        },
        "eth1": {
            "BIOS device": {"physical": "em2", "all_ethN": "eth1"},
            "Kernel name": "eth1",
            "Permanent MAC": "EC:F4:BB:C3:AF:AA",
            "Assigned MAC": "EC:F4:BB:C3:AF:AA",
            "Driver": "ixgbe",
            "Driver version": "5.9.4",
            "Firmware version": "0x8000095c, 19.5.12",
            "Bus Info": "0000:01:00.1",
            "PCI name": "0000:01:00.1",
            "PCI Slot": "embedded",
            "SMBIOS Device Type": "Ethernet",
            "SMBIOS Instance": "2",
            "SMBIOS Label": "Integrated NIC 2",
            "sysfs Label": "NIC2",
            "Embedded Index": "2",
        },
        "eth2": {
            "BIOS device": {"physical": "em3_1", "all_ethN": "eth2"},
            "Kernel name": "eth2",
            "Permanent MAC": "EC:F4:BB:C3:AF:AC",
            "Assigned MAC": "EC:F4:BB:C3:AF:AC",
            "Driver": "igb",
            "Driver version": "5.3.5.20",
            "Firmware version": "1.67, 0x80000fab, 19.5.12",
            "Bus Info": "0000:07:00.0",
            "PCI name": "0000:07:00.0",
            "PCI Slot": "embedded",
            "SMBIOS Device Type": "Ethernet",
            "SMBIOS Instance": "3",
            "SMBIOS Label": "Integrated NIC 3",
            "sysfs Label": "NIC3",
            "VPD Port": "3",
            "VPD Index": "1",
            "VPD PCI master": "0000:07:00.0",
        },
        "eth3": {
            "BIOS device": {"physical": "em4_1", "all_ethN": "eth3"},
            "Kernel name": "eth3",
            "Permanent MAC": "EC:F4:BB:C3:AF:AD",
            "Assigned MAC": "EC:F4:BB:C3:AF:AD",
            "Driver": "igb",
            "Driver version": "5.3.5.20",
            "Firmware version": "1.67, 0x80000fab, 19.5.12",
            "Bus Info": "0000:07:00.1",
            "PCI name": "0000:07:00.1",
            "PCI Slot": "embedded",
            "SMBIOS Device Type": "Ethernet",
            "SMBIOS Instance": "4",
            "SMBIOS Label": "Integrated NIC 4",
            "sysfs Label": "NIC4",
            "VPD Port": "4",
            "VPD Index": "1",
            "VPD PCI master": "0000:07:00.1",
        },
    }

    def test_without_mock(self):
        """Test all_devices_all_names using PopenWrapper() for Popen(), installed by setUp()"""
        # conftest.py redirects subprocess.Popen("/sbin/biosdevname") to call tests/data/biosdevname
        devices = all_devices_all_names()
        self.assertEqual(
            devices["eth0"]["BIOS device"], {"all_ethN": "eth0", "physical": "em1"}
        )
        self.assertEqual(devices, self.expected_devices)

    def test(self):
        # sourcery skip: extract-method, inline-immediately-returned-variable, path-read
        with patch("xcp.net.biosdevname.Popen") as popen_mock:
            # pylint: disable=unspecified-encoding
            with open("tests/data/physical.biosdevname") as f:
                fake_output_1 = f.read()
            with open("tests/data/all_ethN.biosdevname") as f:
                fake_output_2 = f.read()
            communicate_mock = Mock(side_effect=iter([(fake_output_1, ""),
                                                      (fake_output_2, "")]))
            popen_mock.return_value.communicate = communicate_mock
            popen_mock.return_value.returncode = 0

            devices = all_devices_all_names()

        # check after the fact that we mocked the proper calls
        self.assertEqual(popen_mock.call_count, 2)
        calls = popen_mock.call_args_list
        self.assertEqual(calls[0].args[0], ['/sbin/biosdevname', '--policy', 'physical', '-d'])
        self.assertEqual(calls[1].args[0], ['/sbin/biosdevname', '--policy', 'all_ethN', '-d'])

        self.assertEqual(devices['eth0']['BIOS device'],
                         {'all_ethN': 'eth0', 'physical': 'em1'})
        self.assertEqual(devices, self.expected_devices)