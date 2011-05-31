from django.test import TestCase

from muddle.slots import register, TemplateSlat, ContextSlat
from muddle.slots.registration import MUDDLE_SLOTS


__all__ = ['SlotsRegistration', 'ContextSlatTests', 'TemplateSlatTests']


def func(request):
    pass


def func2(request):
    pass


def func3(request):
    pass


class SlotsTestsBase(TestCase):

    def setUp(self):
        self.tearDown()

    def tearDown(self):
        MUDDLE_SLOTS.clear()


class ContextSlatTests(SlotsTestsBase):

    def test_equality(self):
        """ test equality against other slats """
        slat1 = ContextSlat(func)
        slat1a = ContextSlat(func)
        slat2 = ContextSlat(func2)
        self.assertEqual(slat1, slat1a)
        self.assertNotEqual(slat1, slat2)

    def test_equality_function(self):
        """ test equality operator with functions """
        slat1 = ContextSlat(func)
        self.assertEqual(slat1, func)
        self.assertNotEqual(slat1, func2)


class TemplateSlatTests(SlotsTestsBase):
    def test_equality(self):
        """ test equality against other slats """
        slat1 = TemplateSlat('slots/tests/foo1.html')
        slat1a = TemplateSlat('slots/tests/foo1.html')
        slat2 = TemplateSlat('slots/tests/foo2.html')
        self.assertEqual(slat1, slat1a)
        self.assertNotEqual(slat1, slat2)

    def test_equality_function(self):
        """ test equality operator with functions """
        slat1 = TemplateSlat('slots/tests/foo1.html')
        self.assertEqual(slat1, 'slots/tests/foo1.html')
        self.assertNotEqual(slat1, 'not_same_template.html')


class SlotsRegistration(SlotsTestsBase):

    def test_register_new_slot(self):
        """
        test registering a new slot
        """
        register('foo', TemplateSlat('slots/tests/foo1.html'), ContextSlat(func))
        register('bar', TemplateSlat('slots/tests/foo1.html'), ContextSlat(func))

        self.assertTrue('foo' in MUDDLE_SLOTS)
        self.assertTrue('bar' in MUDDLE_SLOTS)

        self.assertEqual(1, len(MUDDLE_SLOTS['foo'].context_slats))
        self.assertEqual(1, len(MUDDLE_SLOTS['foo'].template_slats))
        self.assertEqual(1, len(MUDDLE_SLOTS['bar'].context_slats))
        self.assertEqual(1, len(MUDDLE_SLOTS['bar'].template_slats))

    def test_register_empty_slot(self):
        """
        test registering a slot with no slats
        """
        register('foo')
        self.assertTrue('foo' in MUDDLE_SLOTS)

    def test_register_existing_slot(self):
        """
        test registering slats in an existing Slot
        """
        self.test_register_new_slot()

        register('foo', TemplateSlat('slots/tests/foo2.html'), ContextSlat(func2))
        register('bar', TemplateSlat('slots/tests/foo2.html'), ContextSlat(func2))

        self.assertTrue('foo' in MUDDLE_SLOTS)
        self.assertTrue('bar' in MUDDLE_SLOTS)
        self.assertEqual(2, len(MUDDLE_SLOTS['foo'].context_slats))
        self.assertEqual(2, len(MUDDLE_SLOTS['foo'].template_slats))
        self.assertEqual(2, len(MUDDLE_SLOTS['bar'].context_slats))
        self.assertEqual(2, len(MUDDLE_SLOTS['bar'].template_slats))

    def test_register_combine_context_slats(self):
        """
        Test that context slats are combined correctly when adding multiple
        context slats
        """
        register('foo', ContextSlat(func), ContextSlat(func2))
        register('foo', ContextSlat(func2), ContextSlat(func3))
        
        slats = MUDDLE_SLOTS['foo'].context_slats
        self.assertTrue(func in slats)
        self.assertTrue(func2 in slats)
        self.assertTrue(func3 in slats)
        self.assertEqual(3, len(slats))

    def test_register_combine_template_slats(self):
        """
        Tests that template slats are combined properly when adding multiple
        template slats
        """
        register('foo', TemplateSlat('slots/tests/foo1.html'))
        register('foo', TemplateSlat('slots/tests/foo2.html'))
        register('foo', TemplateSlat('slots/tests/foo2.html'))
        register('foo', TemplateSlat('slots/tests/foo3.html'))

        slats = MUDDLE_SLOTS['foo'].template_slats
        self.assertTrue('slots/tests/foo1.html' in slats)
        self.assertTrue('slots/tests/foo2.html' in slats)
        self.assertTrue('slots/tests/foo3.html' in slats)
        self.assertEqual(3, len(slats))