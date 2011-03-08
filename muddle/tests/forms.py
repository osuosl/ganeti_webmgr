from django import forms
from django.test import TestCase
from muddle.forms.aggregate import AggregateForm


class Foo(forms.Form):

    one = forms.BooleanField()
    two = forms.CharField(initial='two!')
    three = forms.CharField(required=True)

class Bar(forms.Form):
    two = forms.CharField(required=False)
    three = forms.BooleanField(required=False, initial='three!')
    four = forms.BooleanField()


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
        raise NotImplementedError

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
        raise NotImplementedError

    def test_is_valid_false(self):
        """
        Test when is_valid returns not successful
        """
        raise NotImplementedError

    def test_(self):
        raise NotImplementedError