from django.test import TestCase
from django.test.client import RequestFactory

from django_test_tools.views import ViewTestMixin
from django_test_tools.users import UserTestMixin

from ganeti_web import models
from ganeti_web.models import Node
from ganeti_web.forms.virtual_machine import (vm_wizard, VMWizardView,
                                              VMWizardClusterForm,
                                              VMWizardOwnerForm,
                                              VMWizardBasicsForm,
                                              VMWizardAdvancedForm)

__all__ = [
    "TestVMWizard",
    "TestVMWizardBasicsForm",
    "TestVMWizardAdvancedForm",
]

Cluster = models.Cluster
VirtualMachine = models.VirtualMachine


class MockRapi(object):
    """
    Horrible mock.
    """

    def GetOperatingSystems(self):
        return ["image+dobion-lotso"]


class MockCluster(object):
    """
    Horrible mock.
    """

    info = {
        "enabled_hypervisors": ["kvm", "lxc"],
        "default_hypervisor": "kvm",
        "beparams": {
            "default": {
                "maxmem": 256,
                "vcpus": 1,
            },
        },
        "software_version": "2.6.0",
        "ipolicy": {
            "max": {
                "disk-size": 4096,
                "memory-size": 1024,
            },
            "min": {
                "disk-size": 1024,
                "memory-size": 128,
            },
        },
    }

    rapi = MockRapi()


class TestVMWizard(TestCase, ViewTestMixin, UserTestMixin):
    wizard_url = '/vm/add'

    def setUp(self):
        self.cluster = MockCluster()
        self.user = TestVMWizard.create_user()
        user = self.client.login(username=self.user.username, password='secret')

    def test_form_init(self):
        """
        Tests to make sure our WizardCorrectly initializes the form_list
        """
        forms = (VMWizardClusterForm, VMWizardOwnerForm, VMWizardBasicsForm,
                 VMWizardAdvancedForm)
        # We can't call as_view() here because, that makes the object into a
        # view, which requires a request
        testwizard = VMWizardView.get_initkwargs(forms)
        self.assertEqual(testwizard['form_list'],
            {u'0': VMWizardClusterForm, u'1': VMWizardOwnerForm,
             u'2': VMWizardBasicsForm, u'3': VMWizardAdvancedForm})

    def test_access(self):
        """
        Tests that only authenticated users can access the vm creation wizard
        """
        args = ()
        self.assert_401(self.wizard_url, args)
        self.assert_404(self.wizard_url, args)
        self.assert_200(self.wizard_url, args, [self.user])



class TestVMWizardBasicsForm(TestCase):

    def setUp(self):
        self.cluster = MockCluster()

        self.valid_data = {
            "hv": "kvm",
            "os": "image+dobion-lotso",
            "vcpus": 1,
            "memory": 128,
            "disk_template": "plain",
            "disk_size_0": 2048,
        }

    def test_trivial(self):
        pass

    def test_validate_valid(self):
        form = VMWizardBasicsForm(self.valid_data)
        form._configure_for_cluster(self.cluster)
        self.assertTrue(form.is_valid(), form.errors)

    def test_validate_min_memory(self):
        data = self.valid_data.copy()
        data["memory"] = 64
        form = VMWizardBasicsForm(data)
        form._configure_for_cluster(self.cluster)
        self.assertFalse(form.is_valid(), "Memory should be too small")

    def test_validate_max_memory(self):
        data = self.valid_data.copy()
        data["memory"] = 2048
        form = VMWizardBasicsForm(data)
        form._configure_for_cluster(self.cluster)
        self.assertFalse(form.is_valid(), "Memory should be too big")

    def test_validate_min_disk_size(self):
        data = self.valid_data.copy()
        data["disk_size_0"] = 512
        form = VMWizardBasicsForm(data)
        form._configure_for_cluster(self.cluster)
        self.assertFalse(form.is_valid(), "Disk size should be too small")

    def test_validate_max_disk_size(self):
        data = self.valid_data.copy()
        data["disk_size_0"] = 16384
        form = VMWizardBasicsForm(data)
        form._configure_for_cluster(self.cluster)
        self.assertFalse(form.is_valid(), "Disk size should be too big")

    def test_validate_no_nic_input(self):
        data = self.valid_data.copy()
        data["nics"] = None
        form = VMWizardBasicsForm(data)
        form._configure_for_cluster(self.cluster)
        self.assertTrue(form.is_valid())


class TestVMWizardAdvancedForm(TestCase):

    def setUp(self):
        # XXX #8895 means we need a cluster here
        self.cluster = Cluster()
        self.cluster.hostname = "cluster.example.com"
        self.cluster.save()

        self.pnode = Node()
        self.pnode.cluster = self.cluster
        self.pnode.hostname = "pnode.example.com"
        self.pnode.save()

        self.snode = Node()
        self.snode.cluster = self.cluster
        self.snode.hostname = "snode.example.com"
        self.snode.save()

        self.valid_data = {
            "pnode": self.pnode.id,
            "snode": self.snode.id,
        }

    def tearDown(self):
        self.pnode.delete()
        self.snode.delete()
        self.cluster.delete()

    def test_trivial(self):
        pass

    def test_validate_valid(self):
        form = VMWizardAdvancedForm(self.valid_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_validate_ip_check_without_name_check(self):
        data = self.valid_data.copy()
        data["ip_check"] = True
        form = VMWizardAdvancedForm(data)
        self.assertFalse(form.is_valid(),
                         "IP check shouldn't be allowed without name check")
