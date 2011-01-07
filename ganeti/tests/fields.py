from django.test import TestCase

from ganeti.fields import DataVolumeField
from django.core.exceptions import ValidationError

__all__ = ('TestDataVolumeField',)


class TestDataVolumeField(TestCase):
    def test_to_python(self):
        test_field = DataVolumeField(required=True, min_value=0.)
        # trash
        self.assertRaises(ValidationError, test_field.clean, 'gdrcigeudr7d')
        self.assertRaises(ValidationError, test_field.clean, '     ')
        self.assertRaises(ValidationError, test_field.clean, '')
        test_field.required = False
        self.assertEquals(test_field.clean('     '), None)
        self.assertEquals(test_field.clean(''), None)

        # wrong units
        self.assertRaises(ValidationError, test_field.clean, '100.0 GMB')
        self.assertRaises(ValidationError, test_field.clean, '250 B')
        self.assertRaises(ValidationError, test_field.clean, '50 yogdiecidu')

        # correct
        self.assertEquals(test_field.clean('9001 GB'), 9217024)
        self.assertEquals(test_field.clean('9001.000 GB'), 9217024)
        self.assertEquals(test_field.clean('9001G'), 9217024)
        self.assertEquals(test_field.clean('0.5G'), 512)
        
        self.assertEquals(test_field.clean('100.0 MB'), 100)
        self.assertEquals(test_field.clean('100.00MB'), 100)
        self.assertEquals(test_field.clean('100.000 M'), 100)
        self.assertEquals(test_field.clean('100M'), 100)
