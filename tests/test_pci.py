import sys
import subprocess
import unittest
from mock import patch, Mock

from xcp.pci import PCI, PCIIds, PCIDevices

class TestInvalid(unittest.TestCase):

    def test_invalid_types(self):
        with self.assertRaises(TypeError):
            PCI(0)
        with self.assertRaises(TypeError):
            PCI((0,))
        with self.assertRaises(TypeError):
            PCI([])
        with self.assertRaises(TypeError):
            PCI({})

    def test_invalid_format(self):
        pass

class TestValid(unittest.TestCase):

    def test_null_with_segment(self):

        c = PCI("0000:00:00.0")

        self.assertEqual(c.segment, 0)
        self.assertEqual(c.bus, 0)
        self.assertEqual(c.device, 0)
        self.assertEqual(c.function, 0)

        self.assertEqual(c.integer, 0)


    def test_null_without_segment(self):

        c = PCI("00:00.0")

        self.assertEqual(c.segment, 0)
        self.assertEqual(c.bus, 0)
        self.assertEqual(c.device, 0)
        self.assertEqual(c.function, 0)

        self.assertEqual(c.integer, 0)

    def test_valid(self):

        c = PCI("8765:43:1f.3")

        self.assertEqual(c.segment, 0x8765)
        self.assertEqual(c.bus, 0x43)
        self.assertEqual(c.device, 0x1f)
        self.assertEqual(c.function, 0x3)

    def test_equality(self):

        self.assertEqual(PCI("0000:00:00.0"), PCI("00:00.0"))


class TestPCIIds(unittest.TestCase):
    def tests_nodb(self):
        with patch("xcp.pci.os.path.exists") as exists_mock:
            exists_mock.return_value = False
            with self.assertRaises(Exception):
                PCIIds.read()
        exists_mock.assert_called_once_with("/usr/share/hwdata/pci.ids")

    def tests_videoclass(self):
        with patch("xcp.pci.os.path.exists") as exists_mock, \
             patch("xcp.pci.open") as open_mock, \
             open("tests/data/pci.ids") as fake_data:
            exists_mock.return_value = True
            open_mock.return_value.__iter__ = Mock(return_value=iter(fake_data))
            ids = PCIIds.read()
        exists_mock.assert_called_once_with("/usr/share/hwdata/pci.ids")
        open_mock.assert_called_once_with("/usr/share/hwdata/pci.ids")
        video_class = ids.lookupClass('Display controller')
        self.assertEqual(video_class, ['03'])

        # Python3 Popen().stdout.__iter__ returns bytes. Mock it using mode='rb':
        popen_mode = 'r' if sys.version_info.major == 2 else 'rb'

        with patch("xcp.pci.subprocess.Popen") as popen_mock, \
             open("tests/data/lspci-mn", popen_mode) as fake_data:
            popen_mock.return_value.stdout.__iter__ = Mock(return_value=iter(fake_data))
            devs = PCIDevices()
        popen_mock.assert_called_once_with(['lspci', '-mn'], bufsize = 1,
                                           stdout = subprocess.PIPE)
        sorted_devices = sorted(devs.findByClass(video_class),
                                key=lambda x: x['id'])
        expected = [
            {
                "id": "03:00.0",
                "class": "03",
                "subclass": "80",
                "vendor": "1002",
                "device": "7340",
                "subvendor": "1462",
                "subdevice": "12ac",
            },
            {
                "id": "07:00.0",
                "class": "03",
                "subclass": "00",
                "vendor": "1002",
                "device": "1636",
                "subvendor": "1462",
                "subdevice": "12ac",
            },
        ]
        self.assertEqual(len(sorted_devices), len(expected))
        for device in [0, 1]:
            self.assertDictEqual(expected[device], sorted_devices[device])

        for (video_dev,
             num_functions,
             vendor,
             device,
        ) in zip(sorted_devices,
                 (1, 5),
                 ("Advanced Micro Devices, Inc. [AMD/ATI]",
                  "Advanced Micro Devices, Inc. [AMD/ATI]"),
                 ("Navi 14 [Radeon RX 5500/5500M / Pro 5500M]",
                  "Renoir"),
        ):
            self.assertEqual(len(devs.findRelatedFunctions(video_dev['id'])), num_functions)
            self.assertEqual(ids.findVendor(video_dev['vendor']), vendor)
            self.assertEqual(ids.findDevice(video_dev['vendor'], video_dev['device']), device)

        self.assertEqual(len(devs.findRelatedFunctions('00:18.1')), 7)
