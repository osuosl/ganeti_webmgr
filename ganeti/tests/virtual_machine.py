from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client

from util import client

from ganeti.tests.rapi_proxy import RapiProxy, INSTANCE
from ganeti import models
VirtualMachine = models.VirtualMachine
Cluster = models.Cluster

__all__ = ('TestVirtualMachineModel',)


class TestVirtualMachineModel(TestCase):
    
    def setUp(self):
        self.tearDown()
        models.client.GanetiRapiClient = RapiProxy
    
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
        return vm, cluster
    
    def test_save(self):
        """
        Test saving a VirtualMachine
        
        Verify:
            * VirtualMachine can be saved
            * VirtualMachine can be loaded
            * Hash is copied from cluster
        """
        vm, cluster = self.create_virtual_machine()
        self.assert_(vm.id)
        self.assertFalse(vm.error)
        self.assertEqual(vm.cluster_hash, cluster.hash)
        
        vm = VirtualMachine.objects.get(id=vm.id)
        self.assert_(vm.info)
        self.assertFalse(vm.error)
    
    def test_parse_info(self):
        """
        Test parsing values from cached info
        
        Verifies:
            * mtime and ctime are parsed
            * ram, virtual_cpus, and disksize are parsed
        """
        vm, cluster = self.create_virtual_machine()
        vm.info = INSTANCE
        
        self.assertEqual(vm.ctime, datetime.fromtimestamp(1285799513.4741089))
        self.assertEqual(vm.mtime, datetime.fromtimestamp(1285883187.8692031))
        self.assertEqual(vm.ram, 512)
        self.assertEqual(vm.virtual_cpus, 2)
        self.assertEqual(vm.disk_size, 5120)