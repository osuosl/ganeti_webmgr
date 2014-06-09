from django.template import Context, Template

from ganeti_webmgr.muddle.shots import register, TemplateMixer
from ganeti_webmgr.muddle.shots.tests.registration import ShotsTestsBase

__all__ = ['ShotTagTests']


TEMPLATE = "<b>{% load shots %}{% shot foo %}{% endshot %}</b>"
TEMPLATE_INNER = (
    "<ul>{% load shots %}{% shot foo %}<li>{{mixer}}</li>{% endshot %}</ul>")


class ShotTagTests(ShotsTestsBase):

    def test_no_shot(self):
        text = Template(TEMPLATE).render(Context())
        self.assertEqual("<b></b>", text)

    def test_no_mixers(self):
        register('foo')
        text = Template(TEMPLATE).render(Context())
        self.assertEqual("<b></b>", text)

    def test_single_mixer(self):
        register('foo', TemplateMixer('shots/tests/foo1.html'))
        text = Template(TEMPLATE).render(Context())
        self.assertEqual("<b>foo1</b>", text)

    def test_multiple_mixers(self):
        register('foo', TemplateMixer('shots/tests/foo1.html'))
        register('foo', TemplateMixer('shots/tests/foo2.html'))
        text = Template(TEMPLATE).render(Context())
        self.assertEqual("<b>foo1foo2</b>", text)

    def test_inner_content(self):
        """
        tests {% shot %} with inner content to wrap shots around
        """
        register('foo', TemplateMixer('shots/tests/foo1.html'))
        register('foo', TemplateMixer('shots/tests/foo2.html'))
        text = Template(TEMPLATE_INNER).render(Context())
        self.assertEqual("<ul><li>foo1</li><li>foo2</li></ul>", text)
