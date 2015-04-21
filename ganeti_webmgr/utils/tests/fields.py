# Copyright (C) 2010 Oregon State University et al.
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.

from datetime import datetime
from decimal import Decimal

from django.test import SimpleTestCase

from ..fields import DataVolumeField, MACAddressField, PreciseDateTimeField

__all__ = (
    'TestDataVolumeField',
    'TestMACAddressField',
    "TestPreciseDateTimeField",
)


class TestDataVolumeField(SimpleTestCase):
    """
    DataVolumeField should work.
    """

    def test_dvfield(self):
        valid = {
            "9001 GB": 9217024,
            "9001.000 GB": 9217024,
            "9001G": 9217024,
            "0.5G": 512,
            "100.0 MB": 100,
            "100.00MB": 100,
            "100.000 M": 100,
            "100M": 100,
            100: 100,
            100.1: 100,
            100.9: 100,
            "2 TB": 2097152,
        }
        invalid = {
            "gdrcigeudr7d": [u"Invalid format."],
            "100.0 GMB": [u"Invalid format."],
            "250 B": [u"Invalid format."],
            "50 yogdiecidu": [u"Invalid format."],
        }
        self.assertFieldOutput(DataVolumeField, valid, invalid,
                               empty_value=None)

    def test_dvfield_max_value(self):
        valid = {
            "9000 GB": 9216000,
        }
        invalid = {
            "9001 GB":
            [u"Ensure this value is less than or equal to 9216000."],
        }
        self.assertFieldOutput(DataVolumeField, valid, invalid,
                               field_kwargs={"max_value": 9216000},
                               empty_value=None)


class TestMACAddressField(SimpleTestCase):
    """
    MACAddressField should work.
    """

    def test_mafield(self):
        valid = {
            "aa:bb:cc:dd:ee:ff": "aa:bb:cc:dd:ee:ff",
            "AA:BB:CC:DD:EE:FF": "AA:BB:CC:DD:EE:FF",
            "00-01-02-03-04-05": "00-01-02-03-04-05",
        }
        invalid = {
            "aa:bb:cc:dd:ee:ff:": [u"Enter a valid value."],
            "aa:bb:cc:dd:ee": [u"Enter a valid value."],
            "aa:bb:cc:dd:ee:gg": [u"Enter a valid value."],
            "aa:bb:cc:dd:ee:ff:00": [u"Enter a valid value."],
            "aabbccddeeffaabbc": [u"Enter a valid value."],
        }
        self.assertFieldOutput(MACAddressField, valid, invalid)


class TestPreciseDateTimeField(SimpleTestCase):

    def setUp(self):
        self.f = PreciseDateTimeField()

    def test_trivial(self):
        pass

    def test_to_python_none(self):
        self.assertEqual(self.f.to_python(None), None)

    def test_to_python_datetime(self):
        dt = datetime.now()
        self.assertEqual(self.f.to_python(dt), dt)

    def test_to_python_str(self):
        # The epoch.
        t = "0"
        dt = datetime.fromtimestamp(0)
        self.assertEqual(self.f.to_python(t), dt)

    def test_to_python_decimal(self):
        t = Decimal(0)
        dt = datetime.fromtimestamp(0)
        self.assertEqual(self.f.to_python(t), dt)

    def test_get_prep_value(self):
        dt = datetime.fromtimestamp(0.000001)
        self.assertEqual(self.f.get_prep_value(dt), Decimal("0.000001"))
