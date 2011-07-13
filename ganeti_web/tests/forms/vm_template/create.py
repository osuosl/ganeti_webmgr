from django.test import TestCase

from ganeti_web.forms.vm_template import VirtualMachineTemplateForm
from ganeti_web.models import VirtualMachineTemplate

__all__ = ['TestVirtualMachineTemplateForm']

class TestVirtualMachineTemplateForm(TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_form_init(self):
        """
        Test sanity.
        
        Verifies:
            * Form can be instantiated
            * Form is not bound
        """
        raise NotImplementedError

    def test_form_from_instance(self):
        """
        Test form instantiation from an instance.

        Verifies:
            * Correct instance set
            * All instance fields set
        """
        raise NotImplementedError

    def test_form_from_initial(self):
        """
        Test form instantiation from initial kwarg.
        
        Verifies:
            * Form fields correctly set
            * Form validation is not run
        """
        raise NotImplementedError

    def test_form_from_data(self):
        """
        Test form instantiation from initial kwarg.
        
        Verifies:
            * Form fields correctly set
            * Form validation is not run
        """
        raise NotImplementedError


    def test_form_required_fields(self):
        """
        Test form for required fields.

        Verifies:
            * Form requires correct fields
            * Form has errors when missing required fields
        """
        raise NotImplementedError
