from ganeti_web.forms.vm_template import VirtualMachineTemplateForm
from ganeti_web.models import VirtualMachineTemplate
from ganeti_web.tests.forms.vm_template.base import TemplateTestCase

__all__ = ['TestVirtualMachineTemplateForm']

# See TemplateTestCase for setUp and tearDown. They should be called.
class TestVirtualMachineTemplateForm(TemplateTestCase):
    def test_form_init(self):
        """
        Test sanity.

        Verifies:
            * Form can be instantiated
            * Form is not bound
        """
        for user in self.users:
            form = VirtualMachineTemplateForm(user=user)
            self.assertFalse(form.is_bound)

    def test_form_from_initial(self):
        """
        Test form instantiation from initial kwarg.

        Verifies:
            * Form fields correctly set
            * Form validation is not run
        """
        for user in self.users:
            initial = self.template_data
            form = VirtualMachineTemplateForm(initial=initial, user=user)
            self.assertFalse(form.is_bound)
            self.assertEqual(form.errors, {})
            # A form cannot be validated without being
            #  instantiated with data (arg[0])
            self.assertFalse(form.is_valid())
            for field in initial:
                self.assertTrue(field in form.fields)

    def test_form_from_data(self):
        """
        Test form instantiation from first argument (data).

        Verifies:
            * Form fields correctly set
            * Form validation is run
        """
        for user in self.users:
            data = self.template_data.copy()
            data['cluster'] = self.cluster
            form = VirtualMachineTemplateForm(self.template_data, user=user)
            self.assertTrue(form.is_bound)
            self.assertTrue(form.is_valid())
            for field in self.template_data:
                self.assertTrue(field in form.fields)
                self.assertEqual(data[field], form.cleaned_data[field])


    def test_form_required_fields(self):
        """
        Test form for required fields.

        Verifies:
            * Form requires correct fields
            * Form has errors when missing required fields
        """
        for user in self.users:
            for field in VirtualMachineTemplateForm.Meta.required:
                data = self.template_data.copy()
                del data[field]
                form = VirtualMachineTemplateForm(data, user=user)
                self.assertTrue(field in form.errors)
                self.assertFalse(form.is_valid())

    def test_form_save(self):
        """
        Test form for creation of VirtualMachineTemplate on save

        Verifies:
            * Form has valid data
            * VirtualMachineTemplate is created
        """
        for i, user in enumerate(self.users):
            data = self.template_data.copy()
            template_name = 'template_save_%s' % i
            data['template_name'] = template_name
            self.assertFalse(VirtualMachineTemplate.objects.filter(template_name=template_name).exists())
            form = VirtualMachineTemplateForm(data, user=user)
            self.assertTrue(form.is_bound)
            self.assertTrue(form.is_valid())
            form.save()
            self.assertTrue(VirtualMachineTemplate.objects.filter(template_name=template_name).exists())
