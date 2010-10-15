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
        
        # XXX grant permissions to ensure they exist
        # XXX specify permission manually, it is not auto registering for some reason
        register('admin', VirtualMachine)
        register('start', VirtualMachine)
    
    def tearDown(self):
        VirtualMachine.objects.all().delete()
        Cluster.objects.all().delete()
        User.objects.all().delete()
        UserGroup.objects.all().delete()
    
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

    def test_parse_permissions(self):
        """
        Test parsing permissions from tags:
        
        Verifies:
            * new tags are added to user/group
            * existing tags remain granted
            * removed tags are revoked
        """
        vm, cluster = self.create_virtual_machine()
        
        user0 = User(id=1, username='user0')
        user1 = User(id=2, username='user1')
        user2 = User(id=3, username='user2')
        user0.save()
        user1.save()
        user2.save()
        group0 = UserGroup(id=4, name='group0')
        group1 = UserGroup(id=5, name='group1')
        group2 = UserGroup(id=6, name='group2')
        group0.save()
        group1.save()
        group2.save()
        
        user1.grant('admin', vm)
        user2.grant('admin', vm)
        user2.grant('start', vm)
        group1.grant('admin', vm)
        group2.grant('admin', vm)
        group2.grant('start', vm)
        
        # force info to be parsed
        #
        # user that does not exist - error should be caught
        # group that does not exist - error should be caught
        # permission that does not exist - error should be caught
        data = {}
        data.update(INSTANCE)
        data['tags'] = ['GANETI_WEB_MANAGER:start:U:1',
                        'GANETI_WEB_MANAGER:admin:U:1',
                        'GANETI_WEB_MANAGER:start:U:2',
                        'GANETI_WEB_MANAGER:admin:G:4',
                        'GANETI_WEB_MANAGER:start:G:4',
                        'GANETI_WEB_MANAGER:start:G:5',
                        'GANETI_WEB_MANAGER:bad_perm:U:1',
                        'GANETI_WEB_MANAGER:bad_perm:G:4']
        vm.info = data
        
        # user with new permissions
        self.assertEqual(['admin','start'], user0.get_perms(vm))
        
        # user with a granted and revoked permission
        self.assertEqual(['start'], user1.get_perms(vm))
        
        # group with new permissions
        self.assertEqual(['admin','start'], group0.get_perms(vm))
        
        # group with a granted and revoked permission
        self.assertEqual(['start'], group1.get_perms(vm))
        
        # user with all permissions revoked
        self.assertEqual([], user2.get_perms(vm))
        
        # group with all permissions revoked
        self.assertEqual([], group2.get_perms(vm))

    def test_granting_permissions(self):
        """
        Test granting permissions:
        
        Verifies:
            * granted permission is added to tags and pushed to ganeti
        """
        raise NotImplementedError

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
        group = UserGroup(name='testing_group')
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
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, template)
        
        # authorized user (superuser)
        user.revoke('admin', vm)
        user.is_superuser = True
        user.save()
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
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
        user.revoke('admin', vm)
        
        # authorized (cluster admin)
        grant(user, 'admin', cluster)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'virtual_machine/detail.html')
        user.revoke('admin', cluster)
        
        # authorized (superuser)
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
        user.revoke('admin', vm)
        
        # authorized (cluster admin)
        grant(user, 'admin', cluster)
        response = c.post(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        content = json.loads(response.content)
        self.assertEquals(1, content[0])
        user.revoke('admin', cluster)
        
        # authorized (superuser)
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
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'permissions/form.html')
        user.revoke('admin', vm)
        
        # valid GET authorized user (cluster admin)
        grant(user, 'admin', cluster)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
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
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
        # both user and group
        data = {'permissions':['admin'], 'group':group.id, 'user':user1.id}
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
        # no permissions specified - user
        data = {'permissions':[], 'user':user1.id}
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
        # no permissions specified - group
        data = {'permissions':[], 'group':group.id}
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        
        # valid POST user has permissions
        user1.grant('start', vm)
        data = {'permissions':['admin'], 'user':user1.id}
        response = c.post(url % args, data)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'permissions/user_row.html')
        self.assert_(user1.has_perm('admin', vm))
        self.assertFalse(user1.has_perm('start', vm))
        
        # valid POST group has permissions
        group.grant('start', vm)
        data = {'permissions':['admin'], 'group':group.id}
        response = c.post(url % args, data)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
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
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'permissions/form.html')
        user.revoke('admin', vm)
        
        # valid GET authorized user (cluster admin)
        grant(user, 'admin', cluster)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
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
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
        # no user (POST)
        user1.grant('start', vm)
        data = {'permissions':['admin']}
        response = c.post(url_post % args_post, data)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
        # valid POST user has permissions
        user1.grant('start', vm)
        data = {'permissions':['admin'], 'user':user1.id}
        response = c.post(url_post % args_post, data)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'permissions/user_row.html')
        self.assert_(user1.has_perm('admin', vm))
        self.assertFalse(user1.has_perm('start', vm))
        
        # valid POST user has no permissions left
        data = {'permissions':[], 'user':user1.id}
        response = c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
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
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'permissions/form.html')
        user.revoke('admin', vm)
        
        # valid GET authorized user (cluster admin)
        grant(user, 'admin', cluster)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
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
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
        # no group (POST)
        data = {'permissions':['admin']}
        response = c.post(url_post % args_post, data)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)
        
        # valid POST group has permissions
        group.grant('start', vm)
        data = {'permissions':['admin'], 'group':group.id}
        response = c.post(url_post % args_post, data)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'permissions/group_row.html')
        self.assertEqual(['admin'], group.get_perms(vm))
        
        # valid POST group has no permissions left
        data = {'permissions':[], 'group':group.id}
        response = c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertEqual([], group.get_perms(vm))
        self.assertEqual('1', response.content)