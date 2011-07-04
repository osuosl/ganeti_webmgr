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

from django.test import TestCase

from ganeti_web.fields import DataVolumeField, MACAddressField
from django.core.exceptions import ValidationError

__all__ = [
            'TestDataVolumeFieldToPython',
            'TestMACAddressField'
        ]


class TestDataVolumeFieldToPython(TestCase):
    """
    Test converting DataVolumeField to Python types using the to_python()
    method.
    """

    def setUp(self):
        self.f = DataVolumeField(required=True, min_value=0.)

    def test_trivial(self):
        """
        Check that setUp() is sane.
        """

        pass

    def test_clean_none(self):
        """
        Check that a ValidationError is raised when None is passed in.
        """

        self.assertRaises(ValidationError, self.f.clean, None)

    def test_validationerror(self):
        """
        Make sure that ValidationError is raised when appropriate.
        """

        self.assertRaises(ValidationError, self.f.clean, 'gdrcigeudr7d')
        self.assertRaises(ValidationError, self.f.clean, '     ')
        self.assertRaises(ValidationError, self.f.clean, '')

        # Wrong units?
        self.assertRaises(ValidationError, self.f.clean, '100.0 GMB')
        self.assertRaises(ValidationError, self.f.clean, '250 B')
        self.assertRaises(ValidationError, self.f.clean, '50 yogdiecidu')

    def test_empty_not_required(self):
        """
        Make sure that empty fields clean() to None when a value isn't
        required.
        """

        self.f.required = False
        self.assertEquals(self.f.clean(''), None)
        self.assertEquals(self.f.clean('     '), None)

    def test_correct_values(self):
        """
        Make sure that correct values are generated for valid data.
        """

        self.assertEquals(self.f.clean('9001 GB'), 9217024)
        self.assertEquals(self.f.clean('9001.000 GB'), 9217024)
        self.assertEquals(self.f.clean('9001G'), 9217024)
        self.assertEquals(self.f.clean('0.5G'), 512)
        self.assertEquals(self.f.clean('100.0 MB'), 100)
        self.assertEquals(self.f.clean('100.00MB'), 100)
        self.assertEquals(self.f.clean('100.000 M'), 100)
        self.assertEquals(self.f.clean('100M'), 100)


class TestMACAddressField(TestCase):

    def setUp(self):
        self.f = MACAddressField(required=True)

    def test_trivial(self):
        """
        Check that setUp() is sane.
        """
        pass

    def test_required(self):
        # implicit success, should not throw error
        self.f.validate("aa:bb:cc:dd:ee:ff")

        # required, not given
        self.assertRaises(ValidationError, self.f.validate, None)

        # not required, not given
        self.f.required = False
        self.f.validate(None)


    def test_valid(self):
        self.f.validate("aa:bb:cc:dd:ee:ff")

    def test_invalid(self):
        self.assertRaises(ValidationError, self.f.validate, "aa:bb:cc:dd:ee")
        self.assertRaises(ValidationError, self.f.validate, "aa:bb:cc:dd:ee:ff:00")
        self.assertRaises(ValidationError, self.f.validate, "aa:bb:cc:dd:ee:gg")
        self.assertRaises(ValidationError, self.f.validate, "aabbccddeeffaabbc")
