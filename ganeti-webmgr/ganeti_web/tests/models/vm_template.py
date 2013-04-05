from unittest import TestCase

from ganeti_web.models import VirtualMachineTemplate

__all__ = (
    "TestVirtualMachineTemplateModel",
)

class TestVirtualMachineTemplateModel(TestCase):

    def test_vm_template_set_name_named(self):
        template = VirtualMachineTemplate()

        template.set_name("testing")

        self.assertEqual(template.template_name, "testing")

    def test_vm_template_set_name_temporary(self):
        template = VirtualMachineTemplate()

        template.set_name("")

        self.assertEqual(template.temporary, True)
