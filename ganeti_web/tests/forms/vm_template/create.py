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
        for user in self.users.values():
            form = VirtualMachineTemplateForm(user=user)
            self.assertFalse(form.is_bound)

    def test_form_from_instance(self):
        """
        Test form instantiation from an instance.

        Verifies:
            * Correct instance set
            * All instance fields set
        """
        for user in self.users.values():
            form = VirtualMachineTemplateForm(user=user, instance=self.template)
            self.assertFalse(form.is_bound)
            self.assertTrue(form.is_valid())
            self.assertEqual(form.instance, self.template)
            for field in self.template_fields:
                self.assertEqual(field, form.fields[field].initial)

    def test_form_from_initial(self):
        """
        Test form instantiation from initial kwarg.
        
        Verifies:
            * Form fields correctly set
            * Form validation is not run
        """
        for user in self.users.values():
            form = VirtualMachineTemplateForm(user=user, initial=self.template_data)
            self.assertFalse(form.is_bound)
            for field in form.fields:#self.template_fields:
                self.assertTrue(field in form.fields)
                self.assertEqual(self.template_data[field], form.fields[field].initial)

    def test_form_from_data(self):
        """
        Test form instantiation from first argument (data).
        
        Verifies:
            * Form fields correctly set
            * Form validation is run
        """
        for user in self.users.values():
            form = VirtualMachineTemplateForm(self.template_data, user=user)
            self.assertTrue(form.is_bound)
            self.assertTrue(form.is_valid())


    def test_form_required_fields(self):
        """
        Test form for required fields.

        Verifies:
            * Form requires correct fields
            * Form has errors when missing required fields
        """
        for user in self.users.values():
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
        for i, user in enumerate(self.users.values()):
            data = self.template_data.copy()
            template_name = 'template_save_%s' % i
            data['template_name'] = template_name
            self.assertFalse(VirtualMachineTemplate.objects.filter(template_name=template_name).exists())
            form = VirtualMachineTemplateForm(data, user=user)
            self.assertTrue(form.is_bound)
            self.assertTrue(form.is_valid())
            form.save()
            self.assertTrue(VirtualMachineTemplate.objects.filter(template_name=template_name).exists())
