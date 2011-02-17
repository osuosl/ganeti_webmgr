# vim: set fileencoding=utf8 :
import unittest

from ganeti.templatetags import webmgr_tags as tags

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
