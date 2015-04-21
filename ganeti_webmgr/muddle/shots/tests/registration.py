from django.test import TestCase

from ganeti_webmgr.muddle.shots import register, TemplateMixer
from ganeti_webmgr.muddle.shots.registration import MUDDLE_SHOTS


__all__ = ['ShotsRegistration', 'TemplateMixerTests']


def func(request):
    pass


def func2(request):
    pass


def func3(request):
    pass


class ShotsTestsBase(TestCase):

    def setUp(self):
        self.tearDown()

    def tearDown(self):
        MUDDLE_SHOTS.clear()


class TemplateMixerTests(ShotsTestsBase):
    def test_equality(self):
        """ test equality against other mixers """
        mixer1 = TemplateMixer('shots/tests/foo1.html')
        mixer1a = TemplateMixer('shots/tests/foo1.html')
        mixer2 = TemplateMixer('shots/tests/foo2.html')
        self.assertEqual(mixer1, mixer1a)
        self.assertNotEqual(mixer1, mixer2)

    def test_equality_function(self):
        """ test equality operator with functions """
        mixer1 = TemplateMixer('shots/tests/foo1.html')
        self.assertEqual(mixer1, 'shots/tests/foo1.html')
        self.assertNotEqual(mixer1, 'not_same_template.html')


class ShotsRegistration(ShotsTestsBase):

    def test_register_new_shot(self):
        """
        test registering a new shot
        """
        register('foo', TemplateMixer('shots/tests/foo1.html'))
        register('bar', TemplateMixer('shots/tests/foo1.html'))

        self.assertTrue('foo' in MUDDLE_SHOTS)
        self.assertTrue('bar' in MUDDLE_SHOTS)

        self.assertEqual(1, len(MUDDLE_SHOTS['foo'].template_mixers))
        self.assertEqual(1, len(MUDDLE_SHOTS['bar'].template_mixers))

    def test_register_empty_shot(self):
        """
        test registering a shot with no mixers
        """
        register('foo')
        self.assertTrue('foo' in MUDDLE_SHOTS)

    def test_register_existing_shot(self):
        """
        test registering mixers in an existing Shot
        """
        self.test_register_new_shot()

        register('foo', TemplateMixer('shots/tests/foo2.html'))
        register('bar', TemplateMixer('shots/tests/foo2.html'))

        self.assertTrue('foo' in MUDDLE_SHOTS)
        self.assertTrue('bar' in MUDDLE_SHOTS)
        self.assertEqual(2, len(MUDDLE_SHOTS['foo'].template_mixers))
        self.assertEqual(2, len(MUDDLE_SHOTS['bar'].template_mixers))

    def test_register_combine_template_mixers(self):
        """
        Tests that template mixers are combined properly when adding multiple
        template mixers
        """
        register('foo', TemplateMixer('shots/tests/foo1.html'))
        register('foo', TemplateMixer('shots/tests/foo2.html'))
        register('foo', TemplateMixer('shots/tests/foo2.html'))
        register('foo', TemplateMixer('shots/tests/foo3.html'))

        mixers = MUDDLE_SHOTS['foo'].template_mixers
        self.assertTrue('shots/tests/foo1.html' in mixers)
        self.assertTrue('shots/tests/foo2.html' in mixers)
        self.assertTrue('shots/tests/foo3.html' in mixers)
        self.assertEqual(3, len(mixers))
