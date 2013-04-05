from django.test import TestCase

from ganeti_web.forms.vm_template import VirtualMachineTemplateCopyForm
from ganeti_web.models import VirtualMachineTemplate

__all__ = ['TestVirtualMachineTemplateCopyForm']


data = dict(
    template_name='foobar',
    description='asdf',
)

class TestVirtualMachineTemplateCopyForm(TestCase):
    """
    Test class for testing the use of VirtualMachineTemplateCopyForm
    """
    def test_form_init(self):
        """
        Test sanity.
        
        Verifies:
            * Form can be instantiated
            * Form is not bound
        """
        form = VirtualMachineTemplateCopyForm()
        self.assertFalse(form.is_bound)
        self.assertEqual({}, form.errors)

    def test_form_from_initial(self):
        """
        Test form instantiation from initial kwarg.
        
        Verifies:
            * Form fields correctly set
            * Form validation is not run
        """
        form = VirtualMachineTemplateCopyForm(initial=data)
        self.assertFalse(form.is_bound)
        self.assertEqual({}, form.errors)
        for k, v in data.items():
            self.assertTrue(k in form.initial)
            self.assertEqual(v, form.initial[k])

    def test_form_from_data(self):
        """
        Test form instantiation from initial kwarg.
        
        Verifies:
            * Form fields correctly set
            * Form validation is not
        """
        form = VirtualMachineTemplateCopyForm(data)
        self.assertTrue(form.is_bound)
        self.assertEqual({}, form.errors)
        for k, v in data.items():
            self.assertTrue(k in form.data)
            self.assertEqual(v, form.data[k])


    def test_form_required_fields(self):
        """
        Test form for required fields.

        Verifies:
            * Form requires correct fields
            * Form has errors when missing required fields
        """
        fields = ('template_name',)
        form = VirtualMachineTemplateCopyForm()
        for field in fields:
            self.assertTrue(form.fields[field].required)
        non_req_fields = [f for f in form.fields if f not in fields]
        for field in non_req_fields:
            self.assertFalse(form.fields[field].required)
