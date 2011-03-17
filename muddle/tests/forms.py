from django import forms
from django.test import TestCase
from muddle.forms.aggregate import AggregateForm


class Foo(forms.Form):
    one = forms.BooleanField()
    two = forms.CharField(initial='two!')
    three = forms.CharField(required=True)


class Bar(forms.Form):
    two = forms.CharField(required=False)
    three = forms.CharField(required=False, initial='three!')
    four = forms.BooleanField()


class Xoo(forms.Form):
    five = forms.BooleanField()


class TestAggregateForms(TestCase):
    """ Tests for muddle Aggregate Form class """

    def setUp(self):
        self.tearDown()

    def tearDown(self):
        pass

    def test_aggregate(self):
        """
        Some basic tests to make sure the aggregate method works as intended
        """
        Klass = AggregateForm.aggregate([Foo, Bar])

        # test class members
        self.assertEqual(4, len(Klass.base_fields))
        self.assertTrue('one' in Klass.base_fields)
        self.assertTrue('two' in Klass.base_fields)
        self.assertTrue('three' in Klass.base_fields)
        self.assertTrue('four' in Klass.base_fields)

        # test that required=True always defaults when there are overlapping
        # field names
        self.assertTrue(Klass.base_fields['two'].required)
        self.assertTrue(Klass.base_fields['three'].required)

        # test aggregation of other properties
        self.assertEqual('two!', Klass.base_fields['two'].initial)
        self.assertEqual('three!', Klass.base_fields['three'].initial)

    def test_aggregate_options(self):
        """
        Test that the standard merge can be overridded with options
        """
        options = {
            'one':{'required':False},
            'two': {'initial':'two overridden', 'required':False},
            'three': {'initial':'three overridden', 'required':False}
        }

        Klass = AggregateForm.aggregate([Foo, Bar], options)

        # test class members
        self.assertEqual(4, len(Klass.base_fields))
        self.assertTrue('one' in Klass.base_fields)
        self.assertTrue('two' in Klass.base_fields)
        self.assertTrue('three' in Klass.base_fields)
        self.assertTrue('four' in Klass.base_fields)

        # test that required=True always defaults when there are overlapping
        # field names
        self.assertFalse(Klass.base_fields['two'].required)
        self.assertFalse(Klass.base_fields['three'].required)

        # test aggregation of other properties
        self.assertEqual('two overridden', Klass.base_fields['two'].initial)
        self.assertEqual('three overridden', Klass.base_fields['three'].initial)

        # test property with no conflicts having its properties set by options
        self.assertFalse(Klass.base_fields['one'].required)

    def test_aggregate_incompatible_fields_retype(self):
        """
        Tests creating an aggregate form when a field name is reused but has
        and the types are not the same.
        """
        raise NotImplementedError

    def test_is_valid_true(self):
        """
        Test when is_valid returns successful
        """
        Klass = AggregateForm.aggregate([Foo, Bar])

        data = {
            'one':True,
            'two':"two's value",
            'three':"three's value",
            'four':True,
        }

        form = Klass(data)
        self.assertTrue(form.is_valid())

        data = form.cleaned_data
        self.assertEqual(True, data['one'])
        self.assertEqual("two's value" ,data['two'])
        self.assertEqual("three's value" ,data['three'])
        self.assertEqual(True ,data['four'])

    def test_is_valid_false(self):
        """
        Test when is_valid returns not successful
        """
        options = {'two':{'required':True}, 'three':{'required':True}}
        Klass = AggregateForm.aggregate([Foo, Bar], options)

        data = {
            'one':True,
            'four':True,
        }

        form = Klass(data)
        self.assertFalse(form.is_valid())

        errors = form.errors
        self.assertTrue('two' in errors)
        self.assertTrue('three' in errors)
