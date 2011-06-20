import json

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from ganeti_web.models import SSHKey
from ganeti_web.tests.views.virtual_machine.base import TestVirtualMachineViewsBase

__all__ = ['TestVirtualMachineViewList',
           'TestVirtualMachineDetailView',
           'TestVirtualMachineSSHKeysView']

global c, cluster, vm
global user, user1, superuser, vm_admin, cluster_admin


class TestVirtualMachineViewList(TestVirtualMachineViewsBase):

    context = globals()

    def test_anonymous(self):
        """
        Anonymous users viewing the list of VMs are redirected to the login
        page.
        """
        url = '/vms/'

        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_user(self):
        """
        Users with no VM permissions may view the VM list, but there will be
        no VMs.
        """

        url = '/vms/'

        self.create_virtual_machine(cluster, 'test1')

        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/list.html')
        vms = response.context['vms'].object_list
        # There is (at least) one VM in the list; fail if we can see it.
        self.assertFalse(vms)

    def test_user_permissions(self):
        """
        Users with VM permissions have some VMs in their VM list.
        """

        url = '/vms/'

        # setup vms and perms
        vm1, cluster1 = self.create_virtual_machine(cluster, 'test1')
        self.create_virtual_machine(cluster, 'test2')
        user1.grant('admin', vm)
        user1.grant('admin', vm1)

        # user with some perms
        self.assert_(c.login(username=user1.username, password='secret'))
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/list.html')
        vms = response.context['vms'].object_list
        self.assertEqual(set(vms), set([vm, vm1]))

    def test_superuser(self):
        """
        Superusers see all VMs.
        """

        url = '/vms/'

        user2 = User(id=28, username='tester2', is_superuser=True)
        user2.set_password('secret')
        user2.save()

        # setup vms and perms
        vm1, cluster1 = self.create_virtual_machine(cluster, 'test1')
        vm2, cluster1 = self.create_virtual_machine(cluster, 'test2')
        vm3, cluster1 = self.create_virtual_machine(cluster, 'test3')

        # authorized (superuser)
        self.assert_(c.login(username=user2.username, password='secret'))
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/list.html')
        vms = response.context['vms'].object_list
        self.assertEqual(set(vms), set([vm, vm1, vm2, vm3]))


class TestVirtualMachineDetailView(TestVirtualMachineViewsBase):

    context = globals()

    def test_view_detail(self):
        """
        Test showing virtual machine details
        """
        url = '/cluster/%s/%s/'
        args = (cluster.slug, vm.hostname)

        self.assert_standard_fails(url, args)
        self.assert_200(url, args, [superuser, vm_admin, cluster_admin], template='ganeti/virtual_machine/detail.html')


class TestVirtualMachineSSHKeysView(TestVirtualMachineViewsBase):

    context = globals()

    def test_view_ssh_keys(self):
        """
        Test getting SSH keys belonging to users, who have admin permission on
        specified virtual machine
        """
        # second virtual machine created
        vm1, cluster1 = self.create_virtual_machine(cluster, 'vm2.osuosl.bak')

        # grant admin permission to first user
        user.grant("admin", vm)

        # add some keys
        key = SSHKey(key="ssh-rsa test test@test", user=user)
        key.save()
        key1 = SSHKey(key="ssh-dsa test asd@asd", user=user)
        key1.save()

        # get API key
        import settings
        key = settings.WEB_MGR_API_KEY

        # forbidden
        response = c.get( reverse("instance-keys", args=[cluster.slug, vm.hostname, key+"a"]))
        self.assertEqual( 403, response.status_code )

        # not found
        response = c.get( reverse("instance-keys", args=[cluster.slug, vm.hostname+"a", key]))
        self.assertEqual( 404, response.status_code )
        response = c.get( reverse("instance-keys", args=[cluster.slug+"a", vm.hostname, key]))
        self.assertEqual( 404, response.status_code )

        # vm with users who have admin perms
        response = c.get( reverse("instance-keys", args=[cluster.slug, vm.hostname, key]))
        self.assertEqual( 200, response.status_code )
        self.assertEquals("application/json", response["content-type"])
        self.assertEqual( len(json.loads(response.content)), 2 )
        self.assertContains(response, "test@test", count=1)
        self.assertContains(response, "asd@asd", count=1)

        # vm without users who have admin perms
        response = c.get( reverse("instance-keys", args=[cluster.slug, vm1.hostname, key]))
        self.assertEqual( 200, response.status_code )
        self.assertEquals("application/json", response["content-type"])
        self.assertEqual( len(json.loads(response.content)), 0 )
        self.assertNotContains(response, "test@test")
        self.assertNotContains(response, "asd@asd")