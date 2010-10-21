from datetime import datetime
import json

from django.conf import settings
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import Client

from object_permissions import grant, revoke, register, get_user_perms
from object_permissions.models import ObjectPermission, GroupObjectPermission, \
    UserGroup

from util import client
from ganeti.tests.rapi_proxy import RapiProxy, INSTANCE
from ganeti import models
from ganeti.views.virtual_machine import NewVirtualMachineForm
VirtualMachine = models.VirtualMachine
Cluster = models.Cluster
ClusterUser = models.ClusterUser

__all__ = ('TestVirtualMachineModel', 'TestVirtualMachineViews', 'TestNewVirtualMachineForm')

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
        
        # XXX grant permissions to ensure they exist
        # XXX specify permission manually, it is not auto registering for some reason
        register('admin', VirtualMachine)
        register('start', VirtualMachine)
    
    def tearDown(self):
        VirtualMachine.objects.all().delete()
        Cluster.objects.all().delete()
        User.objects.all().delete()
        UserGroup.objects.all().delete()
        ClusterUser.objects.all().delete()
    
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

    def test_parse_owner(self):
        """
        Tests parsing owner from tags
        """
        vm, cluster = self.create_virtual_machine()
        
        owner0 = ClusterUser(id=1, name='owner0')
        owner1 = ClusterUser(id=2, name='owner1')
        owner0.save()
        owner1.save()
        
        data = INSTANCE.copy()
        self.assertEqual(None, vm.owner)
        
        # set it to a group
        data['tags'] = ['GANETI_WEB_MANAGER:OWNER:%s' % owner0.id]
        vm.info = data
        self.assertEqual(owner0, vm.owner)
        
        # invalid group
        data['tags'] = ['GANETI_WEB_MANAGER:OWNER:%s' % -1]
        vm.info = data
        self.assertEqual(None, vm.owner)
        
        # change it
        data['tags'] = ['GANETI_WEB_MANAGER:OWNER:%s' % owner1.id]
        vm.info = data
        self.assertEqual(owner1, vm.owner)
        
        # set it to None
        data['tags'] = []
        vm.info = data
        self.assertEqual(None, vm.owner)
    
    def test_update_owner_tag(self):
        """
        Test changing owner
        """
        vm, cluster = self.create_virtual_machine()
        
        owner0 = ClusterUser(id=1, name='owner0')
        owner1 = ClusterUser(id=2, name='owner1')
        owner0.save()
        owner1.save()
        
        # no owner
        vm.refresh()
        self.assertEqual([], vm.info['tags'])
        
        # setting owner
        vm.owner = owner0
        vm.save()
        self.assertEqual(['GANETI_WEB_MANAGER:OWNER:%s'%owner0.id], vm.info['tags'])
        
        # changing owner
        vm.owner = owner1
        vm.save()
        self.assertEqual(['GANETI_WEB_MANAGER:OWNER:%s'%owner1.id], vm.info['tags'])
        
        # setting owner to none
        vm.owner = None
        vm.save()
        self.assertEqual([], vm.info['tags'])


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
        group = UserGroup(id=1, name='testing_group')
        group.save()
        
        g = globals()
        g['vm'] = vm
        g['cluster'] = cluster
        g['user'] = user
        g['user1'] = user1
        g['c'] = Client()
        g['group'] = group
        
        # XXX specify permission manually, it is not auto registering for some reason
        register('admin', Cluster)
        register('create_vm', Cluster)
        register('admin', VirtualMachine)
        register('start', VirtualMachine)
    
    def tearDown(self):
        ObjectPermission.objects.all().delete()
        GroupObjectPermission.objects.all().delete()
        UserGroup.objects.all().delete()
        User.objects.all().delete()
        VirtualMachine.objects.all().delete()
        Cluster.objects.all().delete()
    
    def validate_get(self, url, args, template):
        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)
        
        # nonexisent cluster
        response = c.get(url % ("DOES_NOT_EXIST", vm.id))
        self.assertEqual(404, response.status_code)
        
        # nonexisent vm
        response = c.get(url % (cluster.slug, vm.id))
        self.assertEqual(404, response.status_code)
        
        # authorized user (perm)
        grant(user, 'admin', vm)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, template)
        
        # authorized user (superuser)
        user.revoke('admin', vm)
        user.is_superuser = True
        user.save()
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, template)
    
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
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/list.html')
        vms = response.context['vms']
        self.assertFalse(vms)
        
        # user with some perms
        self.assert_(c.login(username=user1.username, password='secret'))
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/list.html')
        vms = response.context['vms']
        self.assert_(vm in vms)
        self.assert_(vm1 in vms)
        self.assertEqual(2, len(vms))
        
        # authorized (superuser)
        self.assert_(c.login(username=user2.username, password='secret'))
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
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
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/detail.html')
        user.revoke('admin', vm)
        
        # authorized (cluster admin)
        grant(user, 'admin', cluster)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/detail.html')
        user.revoke('admin', cluster)
        
        # authorized (superuser)
        user.is_superuser = True
        user.save()
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
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
        self.assertEqual('application/json', response['content-type'])
        content = json.loads(response.content)
        self.assertEqual(1, content[0])
        user.revoke('admin', vm)
        
        # authorized (cluster admin)
        grant(user, 'admin', cluster)
        response = c.post(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        content = json.loads(response.content)
        self.assertEqual(1, content[0])
        user.revoke('admin', cluster)
        
        # authorized (superuser)
        user.is_superuser = True
        user.save()
        response = c.post(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        self.assertEqual(1, content[0])
        
        # error while issuing reboot command
        msg = "SIMULATING_AN_ERROR"
        vm.rapi.error = client.GanetiApiError(msg)
        response = c.post(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        code, text = json.loads(response.content)
        self.assertEqual(msg, text)
        self.assertEqual(0, code)
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
        group1 = UserGroup(id=2, name='testing_group2')
        group1.save()
        cluster1 = Cluster(hostname='test2.osuosl.bak', slug='OSL_TEST2')
        cluster1.save()
        
        # anonymous user
        response = c.get(url % '', follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.post(url % '')
        self.assertEqual(403, response.status_code)
        
        # authorized GET (create_vm permissions)
        user.grant('create_vm', cluster)
        response = c.get(url % '')
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/create.html')
        user.revoke_all(cluster)
        
        # authorized GET (cluster admin permissions)
        user.grant('admin', cluster)
        response = c.get(url % '')
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/create.html')
        user.revoke_all(cluster)
        
        # authorized GET (superuser)
        user.is_superuser = True
        user.save()
        response = c.get(url % '')
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/create.html')
        
        # GET unknown cluster
        response = c.get(url % 'DOES_NOT_EXIST')
        self.assertEqual(404, response.status_code)
        
        # GET valid cluster
        response = c.get(url % cluster.slug)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/create.html')
        
        data = dict(cluster=cluster.id,
                    owner=user.get_profile().id, #XXX remove this
                    hostname='new.vm.hostname',
                    disk_template='plain',
                    disk_size=1000,
                    ram=256,
                    vcpus=2,
                    os='image+ubuntu-lucid',
                    pnode=cluster.nodes()[0],
                    snode=cluster.nodes()[0])
        
        # POST - invalid cluster
        data_ = data.copy()
        data_['cluster'] = -1
        response = c.post(url % '', data_)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/create.html')
        self.assertFalse(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())
        
        # POST - unauthorized for cluster selected (authorized for another)
        user.grant('create_vm', cluster1)
        user.is_superuser = False
        user.save()
        response = c.post(url % '', data_)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/create.html')
        self.assertFalse(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())
        
        # POST - required values
        for property in ['cluster', 'hostname', 'disk_size', 'vcpus', 'pnode', 'os', 'disk_template']:
            data_ = data.copy()
            del data_[property]
            response = c.post(url % '', data_)
            self.assertEqual(200, response.status_code)
            self.assertEqual('text/html; charset=utf-8', response['content-type'])
            self.assertTemplateUsed(response, 'virtual_machine/create.html')
            self.assertFalse(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())
        
        # POST - over ram quota
        profile = user.get_profile()
        cluster.set_quota(profile, dict(ram=1000, disk=2000, virtual_cpus=10))
        vm = VirtualMachine(cluster=cluster, ram=100, disk_size=100, virtual_cpus=2, owner=profile).save()
        data_ = data.copy()
        data_['ram'] = 2000
        response = c.post(url % '', data_)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/create.html')
        self.assertFalse(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())
        
        # POST - over disk quota
        data_ = data.copy()
        data_['disk'] = 2000
        response = c.post(url % '', data_)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/create.html')
        self.assertFalse(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())
        
        # POST - over cpu quota
        data_ = data.copy()
        data_['vcpus'] = 2000
        response = c.post(url % '', data_)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/create.html')
        self.assertFalse(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())
        
        # POST invalid owner
        data_ = data.copy()
        data_['owner'] = -1
        response = c.post(url % '', data_)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/create.html')
        self.assertFalse(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())
        
        # POST - user authorized for cluster (create_vm)
        user.grant('admin', cluster)
        response = c.post(url % '', data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/detail.html')
        new_vm = VirtualMachine.objects.get(hostname='new.vm.hostname')
        self.assertEqual(new_vm, response.context['instance'])
        self.assert_(user.has_perm('admin', new_vm), user.__dict__)
        user.revoke_all(cluster)
        user.revoke_all(new_vm)
        VirtualMachine.objects.all().delete()
        
        # POST - user authorized for cluster (admin)
        user.grant('admin', cluster)
        response = c.post(url % '', data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/detail.html')
        new_vm = VirtualMachine.objects.get(hostname='new.vm.hostname')
        self.assertEqual(new_vm, response.context['instance'])
        self.assert_(user.has_perm('admin', new_vm))
        VirtualMachine.objects.all().delete()
        user.revoke_all(cluster)
        user.revoke_all(new_vm)
        
        # POST - User attempting to be other user
        data_ = data.copy()
        data_['owner'] = user1.get_profile().id
        response = c.post(url % '', data_)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/create.html')
        self.assertFalse(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())
        
        # POST - user authorized for cluster (superuser)
        user.is_superuser = True
        user.save()
        response = c.post(url % '', data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/detail.html')
        new_vm = VirtualMachine.objects.get(hostname='new.vm.hostname')
        self.assertEqual(new_vm, response.context['instance'])
        self.assert_(user.has_perm('admin', new_vm))
        user.revoke_all(new_vm)
        VirtualMachine.objects.all().delete()
        
        # POST - ganeti error
        cluster.rapi.CreateInstance.error = client.GanetiApiError('Testing Error')
        response = c.post(url % '', data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/create.html')
        self.assertFalse(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())
        cluster.rapi.CreateInstance.error = None
        
        # POST - User attempting to be other user (superuser)
        data_ = data.copy()
        data_['owner'] = user1.get_profile().id
        response = c.post(url % '', data_, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/detail.html')
        new_vm = VirtualMachine.objects.get(hostname='new.vm.hostname')
        self.assertEqual(new_vm, response.context['instance'])
        self.assert_(user1.has_perm('admin', new_vm))
        self.assertEqual([], user.get_perms(new_vm))
        
        user.revoke_all(new_vm)
        user1.revoke_all(new_vm)
        VirtualMachine.objects.all().delete()
        
        # reset for group owner
        user.is_superuser = False
        user.save()
        data['owner'] = group.organization.id
        
        # POST - user is not member of group
        group.grant('create_vm', cluster)
        response = c.post(url % '', data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/create.html')
        self.assertFalse(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())
        group.revoke_all(new_vm)
        VirtualMachine.objects.all().delete()
        
        # add user to group
        group.users.add(user)
        
        # POST - group authorized for cluster (create_vm)
        group.grant('create_vm', cluster)
        response = c.post(url % '', data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/detail.html')
        new_vm = VirtualMachine.objects.get(hostname='new.vm.hostname')
        self.assertEqual(new_vm, response.context['instance'])
        self.assert_(group.has_perm('admin', new_vm))
        group.revoke_all(cluster)
        group.revoke_all(new_vm)
        VirtualMachine.objects.all().delete()
        
        # POST - group authorized for cluster (admin)
        group.grant('admin', cluster)
        response = c.post(url % '', data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/detail.html')
        new_vm = VirtualMachine.objects.get(hostname='new.vm.hostname')
        self.assertEqual(new_vm, response.context['instance'])
        self.assert_(group.has_perm('admin', new_vm))
        group.revoke_all(cluster)
        group.revoke_all(new_vm)
        VirtualMachine.objects.all().delete()
        
        # POST - group authorized for cluster (superuser)
        user.is_superuser = True
        user.save()
        response = c.post(url % '', data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/detail.html')
        new_vm = VirtualMachine.objects.get(hostname='new.vm.hostname')
        self.assertEqual(new_vm, response.context['instance'])
        self.assert_(group.has_perm('admin', new_vm))
        group.revoke_all(new_vm)
        VirtualMachine.objects.all().delete()
        
        # POST - not a group member (superuser)
        data_ = data.copy()
        data_['owner'] = group1.organization.id
        response = c.post(url % '', data_, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/detail.html')
        new_vm = VirtualMachine.objects.get(hostname='new.vm.hostname')
        self.assertEqual(new_vm, response.context['instance'])
        self.assert_(group1.has_perm('admin', new_vm))
        self.assertFalse(group.has_perm('admin', new_vm))
    
    def test_view_cluster_choices(self):
        """
        Test retrieving list of clusters a user or usergroup has access to
        """
        url = '/vm/add/choices/'
        Cluster.objects.all().delete()
        cluster0 = Cluster(hostname='user.create_vm', slug='user_create_vm')
        cluster0.save()
        cluster1 = Cluster(hostname='user.admin', slug='user_admin')
        cluster1.save()
        cluster2 = Cluster(hostname='superuser', slug='superuser')
        cluster2.save()
        cluster3 = Cluster(hostname='group.create_vm', slug='group_create_vm')
        cluster3.save()
        cluster4 = Cluster(hostname='group.admin', slug='group_admin')
        cluster4.save()
        cluster5 = Cluster(hostname='no.perms.on.this.group', slug='no_perms')
        cluster5.save()
        # cluster ids are 1 through 6
        
        group.users.add(user)
        group1 = UserGroup(id=2, name='testing_group2')
        group1.save()
        group1.grant('admin',cluster5)
        
        # anonymous user
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        self.assert_(c.login(username=user.username, password='secret'))
        
        # invalid group_id
        response = c.get(url, {'group_id':-1})
        self.assertEqual(404, response.status_code)
        
        # group user is not a member of
        response = c.get(url, {'group_id':2})
        self.assertEqual(403, response.status_code)
        
        
        # create_vm permission (group)
        group.grant('create_vm', cluster3)
        response = c.get(url, {'group_id':1})
        self.assertEqual(200, response.status_code)
        clusters = json.loads(response.content)
        self.assert_([4,'group.create_vm'] in clusters)
        self.assertEqual(1, len(clusters))
        
        # admin permission (group)
        group.grant('admin', cluster4)
        response = c.get(url, {'group_id':1})
        self.assertEqual(200, response.status_code)
        clusters = json.loads(response.content)
        self.assert_([4,'group.create_vm'] in clusters)
        self.assert_([5,'group.admin'] in clusters)
        self.assertEqual(2, len(clusters))
        
        # create_vm permission
        user.grant('create_vm', cluster0)
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        clusters = json.loads(response.content)
        self.assert_([1,'user.create_vm'] in clusters)
        self.assertEqual(1, len(clusters), clusters)
        
        # admin permission
        user.grant('admin', cluster1)
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        clusters = json.loads(response.content)
        self.assert_([1,'user.create_vm'] in clusters)
        self.assert_([2,'user.admin'] in clusters)
        self.assertEqual(2, len(clusters))
        
        # authorized (superuser)
        user.is_superuser = True
        user.save()
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        clusters = json.loads(response.content)
        self.assert_([1,'user.create_vm'] in clusters)
        self.assert_([2,'user.admin'] in clusters)
        self.assert_([3,'superuser'] in clusters, clusters)
        self.assert_([4,'group.create_vm'] in clusters)
        self.assert_([5,'group.admin'] in clusters, clusters)
        self.assert_([6,'no.perms.on.this.group'] in clusters)
        self.assertEqual(6, len(clusters))
    
    def test_view_cluster_options(self):
        """
        Test retrieving list of options a cluster has for vms
        """
        url = '/vm/add/options/?cluster_id=%s'
        args = cluster.id
        
        # anonymous user
        response = c.post(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)
        
        # invalid cluster
        response = c.get(url % "-4")
        self.assertEqual(404, response.status_code)
        
        # authorized (create_vm)
        grant(user, 'create_vm', cluster)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        content = json.loads(response.content)
        self.assertEqual(['gtest1.osuosl.bak', 'gtest2.osuosl.bak'], content['nodes'])
        self.assertEqual(['image+debian-osgeo', 'image+ubuntu-lucid'], content['os'])
        user.revoke_all(cluster)
        
        # authorized (cluster admin)
        grant(user, 'admin', cluster)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        content = json.loads(response.content)
        self.assertEqual(['gtest1.osuosl.bak', 'gtest2.osuosl.bak'], content['nodes'])
        self.assertEqual(['image+debian-osgeo', 'image+ubuntu-lucid'], content['os'])
        user.revoke_all(cluster)
        
        # authorized (superuser)
        user.is_superuser = True
        user.save()
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        content = json.loads(response.content)
        self.assertEqual(['gtest1.osuosl.bak', 'gtest2.osuosl.bak'], content['nodes'])
        self.assertEqual(['image+debian-osgeo', 'image+ubuntu-lucid'], content['os'])
    
    def test_view_users(self):
        """
        Tests view for cluster users:
        
        Verifies:
            * lack of permissions returns 403
            * nonexistent Cluster returns 404
            * nonexistent VirtualMachine returns 404
        """
        url = "/cluster/%s/%s/users/"
        args = (cluster.slug, vm.hostname)
        self.validate_get(url, args, 'permissions/users.html')

    def test_view_add_permissions(self):
        """
        Test adding permissions to a new User or UserGroup
        """
        url = '/cluster/%s/%s/permissions/'
        args = (cluster.slug, vm.hostname)
        
        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)
        
        # nonexisent cluster
        response = c.get(url % ("DOES_NOT_EXIST", vm.hostname))
        self.assertEqual(404, response.status_code)
        
        # nonexisent vm
        response = c.get(url % (cluster.slug, "DOES_NOT_EXIST"))
        self.assertEqual(404, response.status_code)
        
        # valid GET authorized user (perm)
        grant(user, 'admin', vm)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'permissions/form.html')
        user.revoke('admin', vm)
        
        # valid GET authorized user (cluster admin)
        grant(user, 'admin', cluster)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'permissions/form.html')
        user.revoke('admin', cluster)
        
        # valid GET authorized user (superuser)
        user.is_superuser = True
        user.save()
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'permissions/form.html')
        
        # no user or group
        data = {'permissions':['admin']}
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
        # both user and group
        data = {'permissions':['admin'], 'group':group.id, 'user':user1.id}
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
        # no permissions specified - user
        data = {'permissions':[], 'user':user1.id}
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
        # no permissions specified - group
        data = {'permissions':[], 'group':group.id}
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        
        # valid POST user has permissions
        user1.grant('start', vm)
        data = {'permissions':['admin'], 'user':user1.id}
        response = c.post(url % args, data)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'permissions/user_row.html')
        self.assert_(user1.has_perm('admin', vm))
        self.assertFalse(user1.has_perm('start', vm))
        
        # valid POST group has permissions
        group.grant('start', vm)
        data = {'permissions':['admin'], 'group':group.id}
        response = c.post(url % args, data)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'permissions/group_row.html')
        self.assertEqual(['admin'], group.get_perms(vm))

    def test_view_user_permissions(self):
        """
        Tests updating User's permissions
        
        Verifies:
            * anonymous user returns 403
            * lack of permissions returns 403
            * nonexistent cluster returns 404
            * invalid user returns 404
            * invalid group returns 404
            * missing user and group returns error as json
            * GET returns html for form
            * If user/group has permissions no html is returned
            * If user/group has no permissions a json response of -1 is returned
        """
        args = (cluster.slug, vm.hostname, user1.id)
        args_post = (cluster.slug, vm.hostname)
        url = "/cluster/%s/%s/permissions/user/%s"
        url_post = "/cluster/%s/%s/permissions/"
        
        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)
        
        # nonexisent cluster
        response = c.get(url % ("DOES_NOT_EXIST", vm.hostname, user1.id))
        self.assertEqual(404, response.status_code)
        
        # nonexisent vm
        response = c.get(url % (cluster.slug, "DOES_NOT_EXIST", user1.id))
        self.assertEqual(404, response.status_code)
        
        # valid GET authorized user (perm)
        grant(user, 'admin', vm)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'permissions/form.html')
        user.revoke('admin', vm)
        
        # valid GET authorized user (cluster admin)
        grant(user, 'admin', cluster)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'permissions/form.html')
        user.revoke('admin', cluster)
        
        # valid GET authorized user (superuser)
        user.is_superuser = True
        user.save()
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'permissions/form.html')
        
        # invalid user
        response = c.get(url % (cluster.slug, vm.hostname, -1))
        self.assertEqual(404, response.status_code)
        
        # invalid user (POST)
        user1.grant('start', vm)
        data = {'permissions':['admin'], 'user':-1}
        response = c.post(url_post % args_post, data)
        self.assertEqual('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
        # no user (POST)
        user1.grant('start', vm)
        data = {'permissions':['admin']}
        response = c.post(url_post % args_post, data)
        self.assertEqual('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
        # valid POST user has permissions
        user1.grant('start', vm)
        data = {'permissions':['admin'], 'user':user1.id}
        response = c.post(url_post % args_post, data)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'permissions/user_row.html')
        self.assert_(user1.has_perm('admin', vm))
        self.assertFalse(user1.has_perm('start', vm))
        
        # valid POST user has no permissions left
        data = {'permissions':[], 'user':user1.id}
        response = c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        self.assertEqual([], get_user_perms(user, vm))
        self.assertEqual('1', response.content)

    def test_view_group_permissions(self):
        """
        Test editing UserGroup permissions on a Cluster
        """
        args = (cluster.slug, vm.hostname, group.id)
        args_post = (cluster.slug, vm.hostname)
        url = "/cluster/%s/%s/permissions/group/%s"
        url_post = "/cluster/%s/%s/permissions/"
        
        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)
        
        # nonexisent cluster
        response = c.get(url % ("DOES_NOT_EXIST", vm.hostname, group.id))
        self.assertEqual(404, response.status_code)
        
        # nonexisent vm
        response = c.get(url % (cluster.slug, "DOES_NOT_EXIST", user1.id))
        self.assertEqual(404, response.status_code)
        
        # valid GET authorized user (perm)
        grant(user, 'admin', vm)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'permissions/form.html')
        user.revoke('admin', vm)
        
        # valid GET authorized user (cluster admin)
        grant(user, 'admin', cluster)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'permissions/form.html')
        user.revoke('admin', cluster)
        
        # valid GET authorized user (superuser)
        user.is_superuser = True
        user.save()
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'permissions/form.html')
        
        # invalid group
        response = c.get(url % (cluster.slug, vm.hostname, 0))
        self.assertEqual(404, response.status_code)
        
        # invalid group (POST)
        data = {'permissions':['admin'], 'group':-1}
        response = c.post(url_post % args_post, data)
        self.assertEqual('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
        # no group (POST)
        data = {'permissions':['admin']}
        response = c.post(url_post % args_post, data)
        self.assertEqual('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
        # valid POST group has permissions
        group.grant('start', vm)
        data = {'permissions':['admin'], 'group':group.id}
        response = c.post(url_post % args_post, data)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'permissions/group_row.html')
        self.assertEqual(['admin'], group.get_perms(vm))
        
        # valid POST group has no permissions left
        data = {'permissions':[], 'group':group.id}
        response = c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        self.assertEqual([], group.get_perms(vm))
        self.assertEqual('1', response.content)


class TestNewVirtualMachineForm(TestCase, VirtualMachineTestCaseMixin):
    
    def setUp(self):
        self.tearDown()
        models.client.GanetiRapiClient = RapiProxy
        cluster0 = Cluster(hostname='test0', slug='test0')
        cluster1 = Cluster(hostname='test1', slug='test1')
        cluster2 = Cluster(hostname='test2', slug='test2')
        cluster3 = Cluster(hostname='test3', slug='test3')
        cluster0.save()
        cluster1.save()
        cluster2.save()
        cluster3.save()
        
        user = User(id=2, username='tester0')
        user.set_password('secret')
        user.save()
        user1 = User(id=3, username='tester1')
        user1.set_password('secret')
        user1.save()
        group = UserGroup(id=1, name='testing_group')
        group.save()
        
        g = globals()
        g['cluster0'] = cluster0
        g['cluster1'] = cluster1
        g['cluster2'] = cluster2
        g['cluster3'] = cluster3
        g['user'] = user
        g['user1'] = user1
        g['group'] = group
        
        # XXX specify permission manually, it is not auto registering for some reason
        register('admin', Cluster)
        register('create_vm', Cluster)
    
    def tearDown(self):
        ObjectPermission.objects.all().delete()
        GroupObjectPermission.objects.all().delete()
        UserGroup.objects.all().delete()
        User.objects.all().delete()
        VirtualMachine.objects.all().delete()
        Cluster.objects.all().delete()
    
    def test_cluster_init(self):
        """
        Tests initializing a form with a Cluster
        
        Verifies:
            * cluster choices are set correctly
            * node choices are set correctly
        """
        
        # no cluster
        form = NewVirtualMachineForm(user, None)
        self.assertEqual([(u'', u'---------')], form.fields['pnode'].choices)
        self.assertEqual([(u'', u'---------')], form.fields['snode'].choices)
        self.assertEqual([(u'', u'---------')], form.fields['os'].choices)
        
        # cluster provided
        form = NewVirtualMachineForm(user, cluster0)
        self.assertEqual([(u'', u'---------'), ('gtest1.osuosl.bak', 'gtest1.osuosl.bak'), ('gtest2.osuosl.bak', 'gtest2.osuosl.bak')], form.fields['pnode'].choices)
        self.assertEqual([(u'', u'---------'), ('gtest1.osuosl.bak', 'gtest1.osuosl.bak'), ('gtest2.osuosl.bak', 'gtest2.osuosl.bak')], form.fields['snode'].choices)
        self.assertEqual([(u'', u'---------'), ('image+debian-osgeo', 'image+debian-osgeo'), ('image+ubuntu-lucid', 'image+ubuntu-lucid')], form.fields['os'].choices)
        
        # cluster from initial data
        form = NewVirtualMachineForm(user, None, {'cluster':cluster0.id})
        self.assertEqual([(u'', u'---------'), ('gtest1.osuosl.bak', 'gtest1.osuosl.bak'), ('gtest2.osuosl.bak', 'gtest2.osuosl.bak')], form.fields['pnode'].choices)
        self.assertEqual([(u'', u'---------'), ('gtest1.osuosl.bak', 'gtest1.osuosl.bak'), ('gtest2.osuosl.bak', 'gtest2.osuosl.bak')], form.fields['snode'].choices)
        self.assertEqual([(u'', u'---------'), ('image+debian-osgeo', 'image+debian-osgeo'), ('image+ubuntu-lucid', 'image+ubuntu-lucid')], form.fields['os'].choices)
        
        # cluster from initial data
        form = NewVirtualMachineForm(user, cluster0, {'cluster':cluster0.id})
        self.assertEqual([(u'', u'---------'), ('gtest1.osuosl.bak', 'gtest1.osuosl.bak'), ('gtest2.osuosl.bak', 'gtest2.osuosl.bak')], form.fields['pnode'].choices)
        self.assertEqual([(u'', u'---------'), ('gtest1.osuosl.bak', 'gtest1.osuosl.bak'), ('gtest2.osuosl.bak', 'gtest2.osuosl.bak')], form.fields['snode'].choices)
        self.assertEqual([(u'', u'---------'), ('image+debian-osgeo', 'image+debian-osgeo'), ('image+ubuntu-lucid', 'image+ubuntu-lucid')], form.fields['os'].choices)
    
    def test_cluster_choices_init(self):
        """
        Tests that cluster choices are based on User permissions
        
        Verifies:
            * superusers have all Clusters as choices
            * user's and groups only receive clusters they have permissions
              directly on.
        """
        # user with no choices
        form = NewVirtualMachineForm(user, None, initial={'owner':user.get_profile().id})
        self.assertEqual([(u'', u'---------')], list(form.fields['cluster'].choices))
        
        # user with choices
        user.grant('admin', cluster0)
        user.grant('create_vm', cluster1)
        form = NewVirtualMachineForm(user, None, initial={'owner':user.get_profile().id})
        self.assertEqual([(u'', u'---------'), (1, u'test0'), (2, u'test1')], list(form.fields['cluster'].choices))
        
        # group with no choices
        form = NewVirtualMachineForm(user, None, initial={'owner':group.organization.id})
        self.assertEqual([(u'', u'---------')], list(form.fields['cluster'].choices))
        
        # group with choices
        group.grant('admin', cluster2)
        group.grant('create_vm', cluster3)
        form = NewVirtualMachineForm(user, None, initial={'owner':group.organization.id})
        self.assertEqual([(u'', u'---------'), (3, u'test2'), (4, u'test3')], list(form.fields['cluster'].choices))
        
        # user - superuser
        user.is_superuser = True
        user.save()
        form = NewVirtualMachineForm(user, None, initial={'owner':user.get_profile().id})
        self.assertEqual([(u'', u'---------'), (1, u'test0'), (2, u'test1'), (3, u'test2'), (4, u'test3')], list(form.fields['cluster'].choices))
        
        # group - superuser
        form = NewVirtualMachineForm(user, None, initial={'owner':group.organization.id})
        self.assertEqual([(u'', u'---------'), (1, u'test0'), (2, u'test1'), (3, u'test2'), (4, u'test3')], list(form.fields['cluster'].choices))
    
    def test_owner_choices_init(self):
        """
        Tests that owner choices are set based on User permissions
        
        Verifies:
            * superusers have all clusterusers as choices
            * user receives themselves as a choice if they have perms
            * user receives all groups they are a member of
        """
        
        # user with no choices
        form = NewVirtualMachineForm(user, cluster0)
        self.assertEqual([(u'', u'---------')], form.fields['owner'].choices)
        
        # user with perms on self, no groups
        user.grant('admin', cluster0)
        form = NewVirtualMachineForm(user, None)
        self.assertEqual([(u'', u'---------'), (1, u'tester0')], form.fields['owner'].choices)
        user.set_perms(['create_vm'], cluster0)
        form = NewVirtualMachineForm(user, None)
        self.assertEqual([(u'', u'---------'), (1, u'tester0')], form.fields['owner'].choices)
        
        # user with perms on self and groups
        group.users.add(user)
        group.grant('admin', cluster0)
        form = NewVirtualMachineForm(user, None)
        self.assertEqual([(u'', u'---------'), (1, u'testing_group'), (1, u'tester0')], form.fields['owner'].choices)
        user.revoke_all(cluster0)
        
        # user with no perms on self, but groups
        form = NewVirtualMachineForm(user, None)
        self.assertEqual([(u'', u'---------'),(1, u'testing_group')], form.fields['owner'].choices)
        group.set_perms(['create_vm'], cluster0)
        form = NewVirtualMachineForm(user, None)
        self.assertEqual([(u'', u'---------'), (1, u'testing_group')], form.fields['owner'].choices)
        group.revoke_all(cluster0)
        
        # superuser
        user.is_superuser = True
        user.save()
        form = NewVirtualMachineForm(user, None)
        self.assertEqual([(u'', u'---------'), (1, u'tester0'), (2, u'tester1'), (3, u'testing_group')], list(form.fields['owner'].choices))