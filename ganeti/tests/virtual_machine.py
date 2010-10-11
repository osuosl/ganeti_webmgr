from datetime import datetime
import json

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
        vm, cluster = self.create_virtual_machine()
        
        user = User(id=2, username='tester0')
        user.set_password('secret')
        user.save()
        user1 = User(id=3, username='tester1')
        user1.set_password('secret')
        user1.save()
        
        g = globals()
        g['vm'] = vm
        g['cluster'] = cluster
        g['user'] = user
        g['user1'] = user1
        g['c'] = Client()
        
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
        url = '/vms/'
        
        user2 = User(id=4, username='tester2', is_superuser=True)
        user2.set_password('secret')
        user2.save()
        
        # setup vms and perms
        vm1, cluster1 = self.create_virtual_machine(cluster, 'test1')
        vm2, cluster1 = self.create_virtual_machine(cluster, 'test2')
        vm3, cluster1 = self.create_virtual_machine(cluster, 'test3')
        user1.grant('admin', vm)
        user1.grant('admin', vm1)
        
        # anonymous user
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # user with perms on no virtual machines
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/list.html')
        vms = response.context['vms']
        self.assertFalse(vms)
        
        # user with some perms
        self.assert_(c.login(username=user1.username, password='secret'))
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/list.html')
        vms = response.context['vms']
        self.assert_(vm in vms)
        self.assert_(vm1 in vms)
        self.assertEqual(2, len(vms))
        
        # authorized (superuser)
        self.assert_(c.login(username=user2.username, password='secret'))
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/list.html')
        vms = response.context['vms']
        self.assert_(vm in vms)
        self.assert_(vm1 in vms)
        self.assert_(vm2 in vms)
        self.assert_(vm3 in vms)
        self.assertEqual(4, len(vms))
    
    def test_view_detail(self):
        """
        Test showing virtual machine details
        """
        url = '/cluster/%s/%s/'
        args = (cluster.slug, vm.hostname)
        
        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)
        
        # invalid cluster
        response = c.get(url % ("DoesNotExist", vm.hostname))
        self.assertEqual(404, response.status_code)
        
        # invalid vm
        response = c.get(url % (cluster.slug, "DoesNotExist"))
        self.assertEqual(404, response.status_code)
        
        # authorized (permission)
        grant(user, 'admin', vm)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/detail.html')
        
        # authorized (superuser)
        user.revoke('admin', vm)
        user.is_superuser = True
        user.save()
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/detail.html')
    
    def validate_post_only_url(self, url, args=None):
        """
        generic function for testing urls that post with no data
        """
        args = args if args else (cluster.slug, vm.hostname)
        
        # anonymous user
        response = c.post(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.post(url % args)
        self.assertEqual(403, response.status_code)
        
        # invalid cluster
        response = c.post(url % ("DoesNotExist", vm.hostname))
        self.assertEqual(404, response.status_code)
        
        # invalid vm
        response = c.post(url % (cluster.slug, "DoesNotExist"))
        self.assertEqual(404, response.status_code)
        
        # authorized (permission)
        grant(user, 'admin', vm)
        response = c.post(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        content = json.loads(response.content)
        self.assertEquals(1, content[0])
        
        # authorized (superuser)
        user.revoke('admin', vm)
        user.is_superuser = True
        user.save()
        response = c.post(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertEquals(1, content[0])
        
        # error while issuing reboot command
        msg = "SIMULATING_AN_ERROR"
        vm.rapi.error = client.GanetiApiError(msg)
        response = c.post(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        code, text = json.loads(response.content)
        self.assertEquals(msg, text)
        self.assertEquals(0, code)
        vm.rapi.error = None
        
        # invalid method
        response = c.get(url % args)
        self.assertEqual(405, response.status_code)
    
    def test_view_startup(self):
        """
        Test starting a virtual machine
        """
        self.validate_post_only_url('/cluster/%s/%s/startup')
    
    def test_view_shutdown(self):
        """
        Test shutting down a virtual machine
        """
        self.validate_post_only_url('/cluster/%s/%s/shutdown')
    
    def test_view_reboot(self):
        """
        Test rebooting a virtual machine
        """
        self.validate_post_only_url('/cluster/%s/%s/reboot')
    
    def test_view_create(self):
        """
        Test creating a virtual machine
        """
        url = '/vm/add/%s'
        
        # GET
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        
        response = c.get(url % (cluster.slug))
        self.assertEqual(200, response.status_code)
        
        # POST
        raise NotImplementedError