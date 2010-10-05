from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client

from object_permissions import grant, revoke, register
from object_permissions.models import ObjectPermission

from util import client
from ganeti.tests.rapi_proxy import RapiProxy, INSTANCE
from ganeti import models
VirtualMachine = models.VirtualMachine
Cluster = models.Cluster

__all__ = ('TestVirtualMachineModel', 'TestVirtualMachineViews')

class VirtualMachineTestCaseMixin():
    def create_virtual_machine(self, cluster=None, hostname='vm1.osuosl.bak'):
        cluster = cluster if cluster else Cluster(hostname='test.osuosl.bak', slug='OSL_TEST')
        cluster.save()
        vm = VirtualMachine(cluster=cluster, hostname=hostname)
        vm.save()
        return vm, cluster


class TestVirtualMachineModel(TestCase, VirtualMachineTestCaseMixin):

    def setUp(self):
        self.tearDown()
        models.client.GanetiRapiClient = RapiProxy
    
    def tearDown(self):
        VirtualMachine.objects.all().delete()
        Cluster.objects.all().delete()
        User.objects.all().delete()
    
    def test_trivial(self):
        """
        Test instantiating a VirtualMachine
        """
        VirtualMachine()
    
    
    
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
    
    def test_hash_update(self):
        """
        When cluster is saved hash for its VirtualMachines should be updated
        """
        vm0, cluster = self.create_virtual_machine()
        vm1, cluster = self.create_virtual_machine(cluster, 'test2.osuosl.bak')
        
        self.assertEqual(vm0.cluster_hash, cluster.hash)
        self.assertEqual(vm1.cluster_hash, cluster.hash)
        
        # change cluster's hash
        cluster.hostname = 'SomethingDifferent'        
        cluster.save()
        vm0 = VirtualMachine.objects.get(pk=vm0.id)
        vm1 = VirtualMachine.objects.get(pk=vm1.id)
        self.assertEqual(vm0.cluster_hash, cluster.hash, 'VirtualMachine does not have updated cache')
        self.assertEqual(vm1.cluster_hash, cluster.hash, 'VirtualMachine does not have updated cache')
    
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


class TestVirtualMachineViews(TestCase, VirtualMachineTestCaseMixin):
    """
    Tests for views showing virtual machines
    """
    
    def setUp(self):
        self.tearDown()
        models.client.GanetiRapiClient = RapiProxy
        self.vm, self.cluster = self.create_virtual_machine()
        
        self.user = User(id=2, username='tester0')
        self.user.set_password('secret')
        self.user.save()
        self.user1 = User(id=3, username='tester1')
        self.user1.set_password('secret')
        self.user1.save()
        
        # XXX specify permission manually, it is not auto registering for some reason
        register('admin', Cluster)
        register('admin', VirtualMachine)
    
    def tearDown(self):
        ObjectPermission.objects.all().delete()
        User.objects.all().delete()
        VirtualMachine.objects.all().delete()
        Cluster.objects.all().delete()
    
    def test_view_list(self):
        """
        Test listing all virtual machines
        """
        user = self.user
        cluster = self.cluster
        vm = self.vm
        url = '/vms/'
        c = Client()
        
        # anonymous user
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        # XXX no permission check implemented for cluster detail
        # response = c.get(url % (cluster.slug, vm.hostname))
        # self.assertEqual(403, response.status_code)
        
        # authorized (superuser)
        user.revoke('admin', vm)
        user.is_superuser = True
        user.save()
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/list.html')
    
    def test_view_detail(self):
        """
        Test showing virtual machine details
        """
        user = self.user
        cluster = self.cluster
        vm = self.vm
        url = '/cluster/%s/%s/'
        c = Client()
        
        # anonymous user
        response = c.get(url % (cluster.slug, vm.hostname), follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        # XXX no permission check implemented for cluster detail
        # response = c.get(url % (cluster.slug, vm.hostname))
        # self.assertEqual(403, response.status_code)
        
        # invalid cluster
        response = c.get(url % ("DoesNotExist", vm.hostname))
        self.assertEqual(404, response.status_code)
        
        # invalid vm
        response = c.get(url % (cluster.slug, "DoesNotExist"))
        self.assertEqual(404, response.status_code)
        
        # authorized (permission)
        grant(user, 'admin', vm)
        response = c.get(url % (cluster.slug, vm.hostname))
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/detail.html')
        
        # authorized (superuser)
        user.revoke('admin', vm)
        user.is_superuser = True
        user.save()
        response = c.get(url % (cluster.slug, vm.hostname))
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/detail.html')
    
    def test_view_startup(self):
        """
        Test starting a virtual machine
        """
        user = self.user
        cluster = self.cluster
        vm = self.vm
        url = '/cluster/%s/%s/startup'
        c = Client()
        
        # anonymous user
        response = c.get(url % (cluster.slug, vm.hostname), follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        # XXX no permission check implemented for cluster detail
        # response = c.get(url % (cluster.slug, vm.hostname))
        # self.assertEqual(403, response.status_code)
        
        # invalid cluster
        response = c.get(url % ("DoesNotExist", vm.hostname))
        self.assertEqual(404, response.status_code)
        
        # invalid vm
        response = c.get(url % (cluster.slug, "DoesNotExist"))
        self.assertEqual(404, response.status_code)
        
        # authorized (permission)
        grant(user, 'admin', vm)
        response = c.get(url % (cluster.slug, vm.hostname))
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/detail.html')
        
        # authorized (superuser)
        user.revoke('admin', vm)
        user.is_superuser = True
        user.save()
        response = c.get(url % (cluster.slug, vm.hostname))
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/detail.html')
    
    def test_view_shutdown(self):
        """
        Test shutting down a virtual machine
        """
        user = self.user
        cluster = self.cluster
        vm = self.vm
        url = '/cluster/%s/%s/shutdown'
        c = Client()
        
        # anonymous user
        response = c.get(url % (cluster.slug, vm.hostname), follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        # XXX no permission check implemented for cluster detail
        # response = c.get(url % (cluster.slug, vm.hostname))
        # self.assertEqual(403, response.status_code)
        
        # invalid cluster
        response = c.get(url % ("DoesNotExist", vm.hostname))
        self.assertEqual(404, response.status_code)
        
        # invalid vm
        response = c.get(url % (cluster.slug, "DoesNotExist"))
        self.assertEqual(404, response.status_code)
        
        # authorized (permission)
        grant(user, 'admin', vm)
        response = c.get(url % (cluster.slug, vm.hostname))
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/detail.html')
        
        # authorized (superuser)
        user.revoke('admin', vm)
        user.is_superuser = True
        user.save()
        response = c.get(url % (cluster.slug, vm.hostname))
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/detail.html')
    
    def test_view_reboot(self):
        """
        Test rebooting a virtual machine
        """
        user = self.user
        cluster = self.cluster
        vm = self.vm
        url = '/cluster/%s/%s/reboot'
        c = Client()
        
        # anonymous user
        response = c.get(url % (cluster.slug, vm.hostname), follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        # XXX no permission check implemented for cluster detail
        # response = c.get(url % (cluster.slug, vm.hostname))
        # self.assertEqual(403, response.status_code)
        
        # invalid cluster
        response = c.get(url % ("DoesNotExist", vm.hostname))
        self.assertEqual(404, response.status_code)
        
        # invalid vm
        response = c.get(url % (cluster.slug, "DoesNotExist"))
        self.assertEqual(404, response.status_code)
        
        # authorized (permission)
        grant(user, 'admin', vm)
        response = c.get(url % (cluster.slug, vm.hostname))
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/detail.html')
        
        # authorized (superuser)
        user.revoke('admin', vm)
        user.is_superuser = True
        user.save()
        response = c.get(url % (cluster.slug, vm.hostname))
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/detail.html')
    
    def test_view_create(self):
        """
        Test creating a virtual machine
        """
        raise NotImplementedError