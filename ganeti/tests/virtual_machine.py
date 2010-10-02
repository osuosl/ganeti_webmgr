from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client

from util import client

from ganeti.tests.rapi_proxy import RapiProxy
from ganeti import models
VirtualMachine = models.VirtualMachine
Cluster = models.Cluster

__all__ = ('TestVirtualMachineModel',)


class TestVirtualMachineModel(TestCase):
    
    def setUp(self):
        models.client.GanetiRapiClient = RapiProxy
        self.tearDown()
    
    def tearDown(self):
        VirtualMachine.objects.all().delete()
    
    def test_trivial(self):
        """
        Test instantiating a VirtualMachine
        """
        VirtualMachine()
    
    def create_virtual_machine(self):
        cluster = Cluster()
        cluster.save()
        vm = VirtualMachine(cluster=cluster, hostname='test.osuosl.bak')
        vm.save()
        return vm
    
    def test_save(self):
        """
        Test saving a VirtualMachine
        
        Verify:
            * VirtualMachine can be saved
            * VirtualMachine can be loaded
        """
        vm = self.create_virtual_machine()
        self.assert_(vm.id)
        self.assertFalse(vm.error)
        
        vm = VirtualMachine.objects.get(id=vm.id)
        self.assert_(vm.info)
        self.assertFalse(vm.error)
    
    def test_load_info_failed(self):
        """
        Test creating a cluster that cannot connect to the cluster to retrieve
        remote info
        
        Verifies:
            * error message is recorded
            * error is cleared on successful refresh
        """
        vm = self.create_virtual_machine()
        msg = "TEST ERROR"
        
        # force an error to test its capture
        vm.rapi.error = client.GanetiApiError(msg)
        vm.refresh()
        self.assertEqual(msg, vm.error)
        
        # clear the error
        vm.rapi.error = None
        vm.refresh()
        self.assertFalse(vm.error)