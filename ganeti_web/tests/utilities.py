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

from django.test import SimpleTestCase

from ganeti_web.utilities import compare, get_hypervisor
from ganeti_web.util.rapi_proxy import INSTANCE, XEN_PVM_INSTANCE, XEN_HVM_INSTANCE

__all__ = (
    "TestCompare",
    "TestGetHypervisor",
)

class TestCompare(SimpleTestCase):
    """
    compare() is a utility function for comparing things and describing the
    comparison.
    """

    def test_compare_string_set(self):
        self.assertEqual(compare("", "foo"), "set to foo")

    def test_compare_string_removed(self):
        self.assertEqual(compare("bar", ""), "removed")

    def test_compare_string_changed(self):
        self.assertEqual(compare("foo", "bar"), "changed from foo to bar")

    def test_compare_bool_enabled(self):
        self.assertEqual(compare(False, True), "enabled")

    def test_compare_bool_disabled(self):
        self.assertEqual(compare(True, False), "disabled")

    def test_compare_float_increased(self):
        self.assertEqual(compare(-34.0, 53.23),
                         "increased from -34.0 to 53.23")

    def test_compare_float_decreased(self):
        self.assertEqual(compare(53.23, -34.0),
                         "decreased from 53.23 to -34.0")

    def test_compare_int_increased(self):
        self.assertEqual(compare(-4, 0), "increased from -4 to 0")

    def test_compare_int_decreased(self):
        self.assertEqual(compare(2, 0), "decreased from 2 to 0")



class TestGetHypervisor(SimpleTestCase):

    def setUp(self):
        class InfoDispenser(object):
            pass

        self.disp = InfoDispenser()

    def test_get_hypervisor_kvm(self):
        self.disp.info = INSTANCE
        self.assertEqual(get_hypervisor(self.disp), "kvm")

    def test_get_hypervisor_pvm(self):
        self.disp.info = XEN_PVM_INSTANCE
        self.assertEqual(get_hypervisor(self.disp), "xen-pvm")

    def test_get_hypervisor_hvm(self):
        self.disp.info = XEN_HVM_INSTANCE
        self.assertEqual(get_hypervisor(self.disp), "xen-hvm")

    def test_get_hypervisor_unknown(self):
        self.disp.info = {"hvparams": "asdfaf"}
        self.assertEqual(get_hypervisor(self.disp), None)
