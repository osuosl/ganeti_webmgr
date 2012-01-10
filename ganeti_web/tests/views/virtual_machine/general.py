import json

from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from ganeti_web.models import SSHKey
from ganeti_web.tests.views.virtual_machine.base import TestVirtualMachineViewsBase

__all__ = ['TestVirtualMachineViewList',
           'TestVirtualMachineDetailView',
           'TestVirtualMachineSSHKeysView']


class TestVirtualMachineViewList(TestVirtualMachineViewsBase):

    def test_anonymous(self):
        """
        Anonymous users viewing the list of VMs are redirected to the login
        page.
        """
        url = '/vms/'

        response = self.c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_user(self):
        """
        Users with no VM permissions may view the VM list, but there will be
        no VMs.
        """

        url = '/vms/'

        self.create_virtual_machine(self.cluster, 'test1')

        self.assertTrue(self.c.login(username=self.user.username,
                                     password='secret'))
        response = self.c.get(url)
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
        vm1, cluster1 = self.create_virtual_machine(self.cluster, 'test1')
        self.create_virtual_machine(self.cluster, 'test2')
        self.user1.grant('admin', self.vm)
        self.user1.grant('admin', vm1)

        # user with some perms
        self.assertTrue(self.c.login(username=self.user1.username,
                                     password='secret'))
        response = self.c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/list.html')
        vms = response.context['vms'].object_list
        self.assertEqual(set(vms), set([self.vm, vm1]))

    def test_superuser(self):
        """
        Superusers see all VMs.
        """

        url = '/vms/'

        user2 = User(id=28, username='tester2', is_superuser=True)
        user2.set_password('secret')
        user2.save()

        # setup vms and perms
        vm1, cluster1 = self.create_virtual_machine(self.cluster, 'test1')
        vm2, cluster1 = self.create_virtual_machine(self.cluster, 'test2')
        vm3, cluster1 = self.create_virtual_machine(self.cluster, 'test3')

        # authorized (superuser)
        self.assertTrue(self.c.login(username=user2.username, password='secret'))
        response = self.c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/list.html')
        vms = response.context['vms'].object_list
        self.assertEqual(set(vms), set([self.vm, vm1, vm2, vm3]))


class TestVirtualMachineDetailView(TestVirtualMachineViewsBase):

    def test_view_detail(self):
        """
        Test showing virtual machine details
        """
        url = '/cluster/%s/%s/'
        args = (self.cluster.slug, self.vm.hostname)

        self.assert_standard_fails(url, args)
        self.assert_200(url, args, [self.superuser, self.vm_admin,
                                    self.cluster_admin],
                        template='ganeti/virtual_machine/detail.html')


class TestVirtualMachineSSHKeysView(TestVirtualMachineViewsBase):

    def test_view_ssh_keys(self):
        """
        Test getting SSH keys belonging to users, who have admin permission on
        specified virtual machine
        """
        # second virtual machine created
        vm1, cluster1 = self.create_virtual_machine(self.cluster, 'vm2.osuosl.bak')

        # grant admin permission to first user
        self.user.grant("admin", self.vm)

        # add some keys
        key = SSHKey(key="ssh-rsa test test@test", user=self.user)
        key.save()
        key1 = SSHKey(key="ssh-dsa test asd@asd", user=self.user)
        key1.save()

        # get API key
        import settings
        key = settings.WEB_MGR_API_KEY

        # forbidden
        response = self.c.get(reverse("instance-keys",
                                      args=[self.cluster.slug,
                                            self.vm.hostname, key+"a"]))
        self.assertEqual(403, response.status_code)

        # not found
        response = self.c.get(reverse("instance-keys",
                                      args=[self.cluster.slug,
                                            self.vm.hostname+"a", key]))
        self.assertEqual(404, response.status_code)
        response = self.c.get(reverse("instance-keys",
                                      args=[self.cluster.slug+"a",
                                            self.vm.hostname, key]))
        self.assertEqual(404, response.status_code)

        # vm with users who have admin perms
        response = self.c.get(reverse("instance-keys",
                                      args=[self.cluster.slug,
                                            self.vm.hostname, key]))
        self.assertEqual(200, response.status_code)
        self.assertEquals("application/json", response["content-type"])
        self.assertEqual(len(json.loads(response.content)), 2)
        self.assertContains(response, "test@test", count=1)
        self.assertContains(response, "asd@asd", count=1)

        # vm without users who have admin perms
        response = self.c.get(reverse("instance-keys",
                                      args=[self.cluster.slug, vm1.hostname,
                                            key]))
        self.assertEqual(200, response.status_code)
        self.assertEquals("application/json", response["content-type"])
        self.assertEqual(len(json.loads(response.content)), 0 )
        self.assertNotContains(response, "test@test")
        self.assertNotContains(response, "asd@asd")
