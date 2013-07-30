from django.test import TestCase

from clusters.models import Cluster
from nodes.models import Node

from ...forms import VMWizardBasicsForm, VMWizardAdvancedForm

__all__ = [
    "TestVMWizardBasicsForm",
    "TestVMWizardAdvancedForm",
]


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
                "minmem": 128,
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
        "nicparams": {
            "default": {
                "mode": "bridged",
                "link": "br0",
            }
        }
    }

    rapi = MockRapi()


class TestVMWizardBasicsForm(TestCase):

    def setUp(self):
        self.cluster = MockCluster()

        self.valid_data = {
            "hv": "kvm",
            "os": "image+dobion-lotso",
            "vcpus": 1,
            "memory": 128,
            "minram": 128,
            "disk_template": "plain",
            "disk_size_0": 2048,
            'nic_mode_0': 'bridged',
            'nic_link_0': 'br0',
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
        del data['nic_mode_0']
        del data['nic_link_0']
        form = VMWizardBasicsForm(data)
        form._configure_for_cluster(self.cluster)
        self.assertTrue(form.is_valid())

    def test_validate_partial_nic_no_mode(self):
        data = self.valid_data.copy()
        data['nic_mode_0'] = ''
        form = VMWizardBasicsForm(data)
        form._configure_for_cluster(self.cluster)
        self.assertFalse(form.is_valid())

    def test_validate_partial_nic_no_link(self):
        data = self.valid_data.copy()
        data['nic_link_0'] = ''
        form = VMWizardBasicsForm(data)
        form._configure_for_cluster(self.cluster)
        self.assertFalse(form.is_valid())


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

    def test_validate_pnode_equals_snode(self):
        invalid_data = self.valid_data.copy()
        invalid_data["snode"] = invalid_data["pnode"]
        form = VMWizardAdvancedForm(invalid_data)
        self.assertFalse(form.is_valid(),
            "The secondary node cannot be the primary node.")
