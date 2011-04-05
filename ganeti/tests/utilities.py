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

from ganeti.utilities import compare

__all__ = ('TestUtilities',)

class TestUtilities(TestCase):
    def test_compare(self):
        """
        Tests compare utility function
        """
        string1 = "foo"
        string2 = "bar"
        string3 = ""
        int1 = 2
        int2 = 0
        int3 = -4
        float1 = 53.23
        float2 = -34.00
        bool1 = True
        bool2 = False
        none = None
        
        stringRemoved = "removed"
        stringSet = "set to %s"
        stringChanged = "changed from %s to %s"
        boolEnabled = "enabled"
        boolDisabled = "disabled"
        numIncreased = "increased from %s to %s"
        numDecreased = "decreased from %s to %s"

        # String set
        result = compare(string3, string1)
        outcome = stringSet % string1
        self.assertEqual(result, outcome)

        # String removed
        result = compare(string2, string3)
        outcome = stringRemoved
        self.assertEqual(result, outcome)

        # String changed
        result = compare(string1, string2)
        outcome = stringChanged % (string1, string2)
        self.assertEqual(result, outcome)


        # Boolean enabled
        result = compare(bool2, bool1)
        outcome = boolEnabled
        self.assertEqual(result, outcome)

        # Boolean disabled
        result = compare(bool1, bool2)
        outcome = boolDisabled
        self.assertEqual(result, outcome)
    

        # Num increased
        result = compare(float2, float1)
        outcome = numIncreased % (float2, float1)
        self.assertEqual(result, outcome)

        result = compare(int3, int2)
        outcome = numIncreased % (int3, int2)
        self.assertEqual(result, outcome)

        # Num decreased
        result = compare(float1, float2)
        outcome = numDecreased % (float1, float2)
        self.assertEqual(result, outcome)

        result = compare(int1, int2)
        outcome = numDecreased % (int1, int2)
        self.assertEqual(result, outcome)

