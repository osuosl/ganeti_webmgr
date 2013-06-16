from ...forms import VMWizardBasicsForm
from .base import TemplateTestCase

__all__ = ['TestEditTemplateVMBasicForm']


class TestEditTemplateVMBasicForm(TemplateTestCase):
    """
    Test Case for the edit form
    """

    def test_form_initial_with_bad_data(self):
        """
        Test: Edit form fails with bad data
        """

        self.template_data['cluster'] = None

        form = VMWizardBasicsForm(self.template_data)
        self.assertFalse(form.is_valid(), msg=form.errors)
