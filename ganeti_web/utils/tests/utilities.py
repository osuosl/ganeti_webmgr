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

from utils import compare, get_hypervisor, hv_prettify, os_prettify
from utils.proxy.constants import INSTANCE, XEN_PVM_INSTANCE, XEN_HVM_INSTANCE

__all__ = (
    "TestCompare",
    "TestGetHypervisor",
    "TestHvPrettify",
    "TestOSPrettify",
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


class TestHvPrettify(SimpleTestCase):

    def test_prettify_kvm(self):
        self.assertEqual(hv_prettify("kvm"), "KVM")

    def test_prettify_unknown(self):
        self.assertEqual(hv_prettify("unknown"), "unknown")


class TestOSPrettify(SimpleTestCase):

    def test_os_prettify(self):
        """
        Test the os_prettify() helper function.
        """

        # Test a single entry.
        self.assertEqual(os_prettify(["hurp+durp"]),
                         [("Hurp", [("hurp+durp", "Durp")])])

    def test_os_prettify_multiple(self):
        """
        Test os_prettify()'s ability to handle multiple entries, including two
        entries on the same category.
        """

        self.assertEqual(
            os_prettify([
                "image+obonto-hungry-hydralisk",
                "image+fodoro-core",
                "dobootstrop+dobion-lotso",
            ]), [
                ("Dobootstrop", [
                    ("dobootstrop+dobion-lotso", "Dobion Lotso"),
                ]),
                ("Image", [
                    ("image+obonto-hungry-hydralisk",
                        "Obonto Hungry Hydralisk"),
                    ("image+fodoro-core", "Fodoro Core"),
                ]),
            ])

    def test_os_prettify_2517(self):
        """
        Test #2157 compliance.

        This example should still parse, but in a weird way. Better than
        nothing, though.
        """

        self.assertEqual(os_prettify(["debian-pressed+ia32"]),
                         [('Debian-pressed',
                         [('debian-pressed+ia32', 'Ia32')])])

    def test_os_prettify_2517_unknown(self):
        """
        Test #2157 compliance.

        This example wasn't part of the bug; it was constructed to show off
        the fix for #2157.
        """

        self.assertEqual(os_prettify(["deb-ver1", "noop"]),
                         [("Unknown", [("deb-ver1", "deb-ver1"),
                         ("noop", "noop"), ]), ])
