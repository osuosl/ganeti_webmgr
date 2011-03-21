from django.test import TestCase

from muddle.core.forms.aggregate import AggregateForm
from muddle.settings import register
from muddle.settings.registration import SETTINGS
from muddle.tests.forms import Foo, Bar, Xoo


class AppSettingsRegistration(TestCase):

    def setUp(self):
        self.tearDown()

    def tearDown(self):
        SETTINGS.clear()

    def test_register_new_category(self):
        """
        test registering a single top level category
        """
        register('general', Foo)

        self.assertTrue('general' in SETTINGS)
        self.assertTrue('general' in SETTINGS['general'])
        self.assertEqual(Foo, SETTINGS['general']['general'])

    def test_register_second_category(self):
        """
        test registering a second top level category
        """
        register('general', Foo)
        register('bar', Bar)

        self.assertTrue('general' in SETTINGS)
        self.assertTrue('general' in SETTINGS['general'])
        self.assertEqual(Foo, SETTINGS['general']['general'])
        
        self.assertTrue('bar' in SETTINGS)
        self.assertTrue('general' in SETTINGS['bar'])
        self.assertEqual(Bar, SETTINGS['bar']['general'])
    
    def test_register_single_subcategory(self):
        """
        Test registering a single subcategory that is explicitly declared
        """
        register('general', Foo, 'foo')
        register('bar', Bar)

        self.assertTrue('general' in SETTINGS)
        self.assertTrue('foo' in SETTINGS['general'])
        self.assertEqual(Foo, SETTINGS['general']['foo'])

    def test_register_second_subcategory(self):
        """
        Tests registering a subcategory for a category that already has at least
        one subcategory
        """
        register('general', Foo, 'foo')
        register('general', Bar, 'bar')

        self.assertTrue('general' in SETTINGS)
        self.assertTrue('foo' in SETTINGS['general'])
        self.assertEqual(Foo, SETTINGS['general']['foo'])

        self.assertTrue('general' in SETTINGS)
        self.assertTrue('bar' in SETTINGS['general'])
        self.assertEqual(Bar, SETTINGS['general']['bar'])

    def test_register_same_category(self):
        """
        tests merging a form into a category that already exists
        """
        register('general', Foo)
        register('general', Bar)

        self.assertTrue('general' in SETTINGS)
        self.assertTrue('general' in SETTINGS['general'])

        form = SETTINGS['general']['general']
        self.assertTrue(issubclass(form, (AggregateForm,)))
        self.assertTrue(Foo in form.form_classes)
        self.assertTrue(Bar in form.form_classes)

    def test_register_same_category_thrice(self):
        """
        Tests merging a form into a category that already uses an aggregate form
        """
        register('general', Foo)
        register('general', Bar)
        register('general', Xoo)

        self.assertTrue('general' in SETTINGS)
        self.assertTrue('general' in SETTINGS['general'])

        form = SETTINGS['general']['general']
        self.assertTrue(issubclass(form, (AggregateForm,)))
        self.assertTrue(Foo in form.form_classes)
        self.assertTrue(Bar in form.form_classes)
        self.assertTrue(Xoo in form.form_classes)



