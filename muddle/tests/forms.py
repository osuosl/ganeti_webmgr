from django import forms
from django.test import TestCase
from muddle.core.forms.aggregate import AggregateForm


class Foo(forms.Form):
    one = forms.BooleanField(initial=True)
    two = forms.CharField(initial='two!')
    three = forms.CharField(initial='three?', required=True)


class Bar(forms.Form):
    two = forms.CharField(required=False)
    three = forms.CharField(required=False, initial='three!')
    four = forms.BooleanField(initial=False)
    six = forms.CharField(required=False, initial='six!')


class TestAggregateForm(TestCase):
    """
    Muddle's AggregateForm can, in fact, aggregate forms.
    """

    def setUp(self):
        self.cls = AggregateForm.aggregate([Foo, Bar])

    def test_aggregate_members(self):
        self.assertEqual(5, len(self.cls.base_fields))
        self.assertTrue('one' in self.cls.base_fields)
        self.assertTrue('two' in self.cls.base_fields)
        self.assertTrue('three' in self.cls.base_fields)
        self.assertTrue('four' in self.cls.base_fields)

    def test_aggregate_override_required(self):
        self.assertTrue(self.cls.base_fields['two'].required)
        self.assertTrue(self.cls.base_fields['three'].required)

    def test_aggregate_initial_merge(self):
        """
        AggregateForm merges initial values.
        """

        self.assertEqual('two!', self.cls.base_fields['two'].initial)

    def test_aggregate_initial_override(self):
        """
        AggregateForm overrides initial values.
        """

        self.assertEqual('three!', self.cls.base_fields['three'].initial)

    def test_aggregate_is_valid_true(self):
        """
        Test when is_valid returns successful.
        """

        data = {
            'one':True,
            'two':"two's value",
            'three':"three's value",
            'four':True,
        }

        form = self.cls(data)
        self.assertTrue(form.is_valid())

        data = form.cleaned_data
        self.assertEqual(True, data['one'])
        self.assertEqual("two's value" ,data['two'])
        self.assertEqual("three's value" ,data['three'])
        self.assertEqual(True ,data['four'])


class TestAggregateFormOptions(TestCase):
    """
    AggregateForm can have options passed into it to customize how fields are
    created.
    """

    def setUp(self):
        options = {
            'one': {
                'required': False,
            },
            'two': {
                'initial': 'two overridden',
                'required': False,
            },
            'three': {
                'initial': 'three overridden',
                'required': False,
            },
        }

        self.cls = AggregateForm.aggregate([Foo, Bar], options)

    def test_aggregate_options_initial(self):
        self.assertFalse(self.cls.base_fields['one'].required)

    def test_aggregate_options_members(self):
        self.assertEqual(5, len(self.cls.base_fields))
        self.assertTrue('one' in self.cls.base_fields)
        self.assertTrue('two' in self.cls.base_fields)
        self.assertTrue('three' in self.cls.base_fields)
        self.assertTrue('four' in self.cls.base_fields)

    def test_aggregate_options_override_required(self):
        self.assertFalse(self.cls.base_fields['two'].required)
        self.assertFalse(self.cls.base_fields['three'].required)

    def test_aggregate_options_initial_override(self):
        self.assertEqual('two overridden',
                         self.cls.base_fields['two'].initial)
        self.assertEqual('three overridden',
                         self.cls.base_fields['three'].initial)

    def test_aggregate_options_is_valid_false(self):
        """
        Test when is_valid returns not successful
        """
        options = {'two':{'required':True}, 'three':{'required':True}}
        cls = AggregateForm.aggregate([Foo, Bar], options)

        data = {
            'one':True,
            'four':True,
        }

        form = cls(data)
        self.assertFalse(form.is_valid())

        errors = form.errors
        self.assertTrue('two' in errors)
        self.assertTrue('three' in errors)
