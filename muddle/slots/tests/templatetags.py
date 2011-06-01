from django.template import Context, Template

from muddle.slots import register, TemplateSlat
from muddle.slots.tests.registration import SlotsTestsBase

__all__ = ['SlotTagTests']


TEMPLATE = "<b>{% load slots %}{% slot foo %}{% endslot %}</b>"
TEMPLATE_INNER = "<ul>{% load slots %}{% slot foo %}<li>{{slat}}</li>{% endslot %}</ul>"


class SlotTagTests(SlotsTestsBase):

    def test_no_slot(self):
        text = Template(TEMPLATE).render(Context())
        self.assertEqual("<b></b>", text)

    def test_no_slats(self):
        register('foo')
        text = Template(TEMPLATE).render(Context())
        self.assertEqual("<b></b>", text)

    def test_single_slat(self):
        register('foo', TemplateSlat('slots/tests/foo1.html'))
        text = Template(TEMPLATE).render(Context())
        self.assertEqual("<b>foo1</b>", text)

    def test_multiple_slats(self):
        register('foo', TemplateSlat('slots/tests/foo1.html'))
        register('foo', TemplateSlat('slots/tests/foo2.html'))
        text = Template(TEMPLATE).render(Context())
        self.assertEqual("<b>foo1foo2</b>", text)

    def test_inner_content(self):
        """
        tests {% slot %} with inner content to wrap slots around
        """
        register('foo', TemplateSlat('slots/tests/foo1.html'))
        register('foo', TemplateSlat('slots/tests/foo2.html'))
        text = Template(TEMPLATE_INNER).render(Context())
        self.assertEqual("<ul><li>foo1</li><li>foo2</li></ul>", text)