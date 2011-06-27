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

    def test_truncate_valid(self):
        self.assertEqual(tags.truncate("test", 4), "test")

    def test_truncate_length(self):
        self.assertEqual(tags.truncate("testing", 6), u"testi…")

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
