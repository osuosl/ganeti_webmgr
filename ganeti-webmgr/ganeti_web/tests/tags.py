# -*- coding: utf-8 -*- vim:encoding=utf-8:
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


import unittest

from ganeti_web.templatetags import webmgr_tags as tags

class TestFilters(unittest.TestCase):
    """
    Big test case for all template filters.
    """

    def test_abbreviate_fqdn(self):
        self.assertEqual(tags.abbreviate_fqdn("subdomain.example.com"),
            "subdomain")

    def test_abbreviate_fqdn_abbreviated(self):
        self.assertEqual(tags.abbreviate_fqdn("subdomain"), "subdomain")

    def test_mult(self):
        self.assertEqual(tags.mult(3, 6), 18)

    def test_mult_strings(self):
        self.assertEqual(tags.mult("-3", "6"), -18)

    def test_render_storage(self):
        self.assertEqual(tags.render_storage(1), "1 MiB")
        self.assertEqual(tags.render_storage(1025), "1.00 GiB")
        self.assertEqual(tags.render_storage(1049600), "1.0010 TiB")

    def test_format_part_total(self):
        fpt = tags.format_part_total
        self.assertEqual(fpt(-1, 1), "unknown")
        self.assertEqual(fpt(0, -4), "unknown")
        self.assertEqual(fpt(4000, 100), "3.91 / 0.1")
        self.assertEqual(fpt(1000, 2000), "0.98 / 1.95")
        self.assertEqual(fpt(3000, 5000), "2.93 / 4.88")
        self.assertEqual(fpt(10000, 30000), "9.77 / 29.3")
        self.assertEqual(fpt(500000, 700000), "488.28 / 683.59")
        self.assertEqual(fpt(1024, 2048), "1 / 2")
        self.assertEqual(fpt(5120, 8192), "5 / 8")
        self.assertEqual(fpt(51200, 81920), "50 / 80")
        self.assertEqual(fpt(512, 2048), "0.5 / 2")
        self.assertEqual(fpt(510972, 870910), "499 / 850.5")

    def test_hvs(self):
        self.assertEqual(tags.hvs(["kvm", "xen-hvm"]), ["KVM", "Xen (HVM)"])
