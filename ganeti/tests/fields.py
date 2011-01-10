from django.test import TestCase

from ganeti.fields import DataVolumeField
from django.core.exceptions import ValidationError

__all__ = ('TestDataVolumeFieldToPython',)


class TestDataVolumeFieldToPython(TestCase):
    """
    Test converting DataVolumeField to Python types using the to_python()
    method.
    """

    def setUp(self):
        self.f = DataVolumeField(required=True, min_value=0.)

    def test_trivial(self):
        """
        Check that setUp() is sane.
        """

        pass

    def test_clean_none(self):
        """
        Check that a ValidationError is raised when None is passed in.
        """

        self.assertRaises(ValidationError, self.f.clean, None)

    def test_validationerror(self):
        """
        Make sure that ValidationError is raised when appropriate.
        """

        self.assertRaises(ValidationError, self.f.clean, 'gdrcigeudr7d')
        self.assertRaises(ValidationError, self.f.clean, '     ')
        self.assertRaises(ValidationError, self.f.clean, '')

        # Wrong units?
        self.assertRaises(ValidationError, self.f.clean, '100.0 GMB')
        self.assertRaises(ValidationError, self.f.clean, '250 B')
        self.assertRaises(ValidationError, self.f.clean, '50 yogdiecidu')

    def test_empty_not_required(self):
        """
        Make sure that empty fields clean() to None when a value isn't
        required.
        """

        self.f.required = False
        self.assertEquals(self.f.clean(''), None)
        self.assertEquals(self.f.clean('     '), None)

    def test_correct_values(self):
        """
        Make sure that correct values are generated for valid data.
        """

        self.assertEquals(self.f.clean('9001 GB'), 9217024)
        self.assertEquals(self.f.clean('9001.000 GB'), 9217024)
        self.assertEquals(self.f.clean('9001G'), 9217024)
        self.assertEquals(self.f.clean('0.5G'), 512)
        self.assertEquals(self.f.clean('100.0 MB'), 100)
        self.assertEquals(self.f.clean('100.00MB'), 100)
        self.assertEquals(self.f.clean('100.000 M'), 100)
        self.assertEquals(self.f.clean('100M'), 100)
