from django.contrib.auth.models import Group

from ganeti_web import models
from ganeti_web.models import VirtualMachineTemplate
from ganeti_web.util.rapi_proxy import JOB_RUNNING
from ganeti_web.tests.views.virtual_machine.base import TestVirtualMachineViewsBase
from ganeti_web.util import client

__all__ = ['TestVirtualMachineCreateView', 'TestVirtualMachineRecoverView']

VirtualMachine = models.VirtualMachine
Cluster = models.Cluster


class TestVirtualMachineCreateView(TestVirtualMachineViewsBase):

    def setUp(self):
        super(TestVirtualMachineCreateView, self).setUp()
        self.data = dict(cluster=self.cluster.id,
            start=True,
            owner=self.user.get_profile().id, #XXX remove this
            hostname='new.vm.hostname',
            disk_template='plain',
            disk_count=1,
            disk_size_0=1000,
            memory=256,
            vcpus=2,
            root_path='/',
            nic_type='paravirtual',
            disk_type = 'paravirtual',
            nic_count=1,
            nic_link_0 = 'br43',
            nic_mode_0='routed',
            boot_order='disk',
            os='image+ubuntu-lucid',
            pnode=self.cluster.nodes.all()[0],
            snode=self.cluster.nodes.all()[1])

    def test_view_create_error(self):
        """
        An invalid cluster causes a form error.
        """

        url = '/vm/add/%s'
        data = self.data
        data['cluster'] = -1,
        self.assertTrue(self.c.login(username=self.user.username,
                                     password='secret'))

        self.user.grant('create_vm', self.cluster)
        response = self.c.post(url % '', data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create.html')
        self.assertFalse(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())

    def test_view_create_data(self):

        url = '/vm/add/%s'
        group1 = Group(id=81, name='testing_group2')
        group1.save()
        cluster1 = Cluster(hostname='test2.osuosl.bak', slug='OSL_TEST2')
        cluster1.save()
        data = self.data

        # Login and grant user.
        self.assertTrue(self.c.login(username=self.user.username,
                                     password='secret'))
        self.user.grant('create_vm', self.cluster)
        self.cluster.set_quota(self.user.get_profile(), dict(ram=1000,
                                                             disk=2000,
                                                             virtual_cpus=10))

        # POST - user authorized for cluster (create_vm)
        self.user.grant('create_vm', self.cluster)
        data_ = data.copy()
        self.assertFalse(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())
        response = self.c.post(url % '', data_, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create_status.html')
        new_vm = VirtualMachine.objects.get(hostname='new.vm.hostname')
        self.assertEqual(new_vm, response.context['instance'])
        self.assertTrue(self.user.has_perm('admin', new_vm))
        self.user.revoke_all(self.cluster)
        self.user.revoke_all(new_vm)
        VirtualMachine.objects.all().delete()

        # POST - user authorized for cluster (admin)
        self.user.grant('admin', self.cluster)
        response = self.c.post(url % '', data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create_status.html')
        new_vm = VirtualMachine.objects.get(hostname='new.vm.hostname')
        self.assertEqual(new_vm, response.context['instance'])
        self.assertTrue(self.user.has_perm('admin', new_vm))
        VirtualMachine.objects.all().delete()
        self.user.revoke_all(self.cluster)
        self.user.revoke_all(new_vm)

        # POST - User attempting to be other user
        self.user.grant('admin', self.cluster)
        data_ = data.copy()
        data_['owner'] = self.user1.get_profile().id
        response = self.c.post(url % '', data_)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create.html')
        self.assertFalse(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())
        self.user.revoke_all(self.cluster)

        # POST - user authorized for cluster (superuser)
        self.user.is_superuser = True
        self.user.save()
        response = self.c.post(url % '', data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create_status.html')
        new_vm = VirtualMachine.objects.get(hostname='new.vm.hostname')
        self.assertEqual(new_vm, response.context['instance'])
        self.assertTrue(self.user.has_perm('admin', new_vm))
        self.user.revoke_all(new_vm)
        VirtualMachine.objects.all().delete()

        # POST - ganeti error
        self.cluster.rapi.CreateInstance.error = client.GanetiApiError('Testing Error')
        response = self.c.post(url % '', data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create.html')
        self.assertFalse(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())
        self.cluster.rapi.CreateInstance.error = None

        # POST - User attempting to be other user (superuser)
        data_ = data.copy()
        data_['owner'] = self.user1.get_profile().id
        response = self.c.post(url % '', data_, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create_status.html')
        new_vm = VirtualMachine.objects.get(hostname='new.vm.hostname')
        self.assertEqual(new_vm, response.context['instance'])
        self.assertTrue(self.user1.has_perm('admin', new_vm))
        self.assertEqual([], self.user.get_perms(new_vm))

        self.user.revoke_all(new_vm)
        self.user1.revoke_all(new_vm)
        VirtualMachine.objects.all().delete()

        # reset for group owner
        self.user.is_superuser = False
        self.user.save()
        data['owner'] = self.group.organization.id

        # POST - user is not member of group
        self.user.grant('admin', self.cluster)
        self.group.grant('create_vm', self.cluster)
        self.assertFalse(self.group in self.user.groups.all())
        response = self.c.post(url % '', data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create.html')
        self.assertFalse(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())
        self.user.revoke_all(self.cluster)
        self.group.revoke_all(self.cluster)
        VirtualMachine.objects.all().delete()

        # add user to group
        self.group.user_set.add(self.user)

        # POST - group authorized for cluster (create_vm)
        self.group.grant('create_vm', self.cluster)
        response = self.c.post(url % '', data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create_status.html')
        new_vm = VirtualMachine.objects.get(hostname='new.vm.hostname')
        self.assertEqual(new_vm, response.context['instance'])
        self.assertTrue(self.group.has_perm('admin', new_vm))
        self.group.revoke_all(self.cluster)
        self.group.revoke_all(new_vm)
        VirtualMachine.objects.all().delete()

        # POST - group authorized for cluster (admin)
        self.group.grant('admin', self.cluster)
        response = self.c.post(url % '', data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create_status.html')
        new_vm = VirtualMachine.objects.get(hostname='new.vm.hostname')
        self.assertEqual(new_vm, response.context['instance'])
        self.assertTrue(self.group.has_perm('admin', new_vm))
        self.group.revoke_all(self.cluster)
        self.group.revoke_all(new_vm)
        VirtualMachine.objects.all().delete()

        # POST - group authorized for cluster (superuser)
        self.user.is_superuser = True
        self.user.save()
        response = self.c.post(url % '', data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create_status.html')
        new_vm = VirtualMachine.objects.get(hostname='new.vm.hostname')
        self.assertEqual(new_vm, response.context['instance'])
        self.assertTrue(self.group.has_perm('admin', new_vm))
        self.group.revoke_all(new_vm)
        VirtualMachine.objects.all().delete()

        # POST - not a group member (superuser)
        data_ = data.copy()
        data_['owner'] = group1.organization.id
        response = self.c.post(url % '', data_, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create_status.html')
        new_vm = VirtualMachine.objects.get(hostname='new.vm.hostname')
        self.assertEqual(new_vm, response.context['instance'])
        self.assertTrue(group1.has_perm('admin', new_vm))
        self.assertFalse(self.group.has_perm('admin', new_vm))

    def test_view_create(self):
        """
        Test viewing the create virtual machine page
        """
        url = '/vm/add/%s'
        group1 = Group(id=87, name='testing_group2')
        group1.save()
        cluster1 = Cluster(hostname='test2.osuosl.bak', slug='OSL_TEST2')
        cluster1.save()

        # anonymous user
        response = self.c.get(url % '', follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assertTrue(self.c.login(username=self.user.username,
                                     password='secret'))
        response = self.c.post(url % '')
        self.assertEqual(403, response.status_code)

        # authorized GET (create_vm permissions)
        self.user.grant('create_vm', self.cluster)
        response = self.c.get(url % '')
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create.html')
        self.user.revoke_all(self.cluster)

        # authorized GET (cluster admin permissions)
        self.user.grant('admin', self.cluster)
        response = self.c.get(url % '')
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create.html')
        self.user.revoke_all(self.cluster)

        # authorized GET (superuser)
        self.user.is_superuser = True
        self.user.save()
        response = self.c.get(url % '')
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create.html')

        # GET unknown cluster
        response = self.c.get(url % 'DOES_NOT_EXIST')
        self.assertEqual(404, response.status_code)

        # GET valid cluster
        response = self.c.get(url % self.cluster.slug)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create.html')


class TestVirtualMachineRecoverView(TestVirtualMachineViewsBase):

    def test_view_create_recover(self):
        """
        Test the create view when recovering a failed vm

        Verifies:
            * vm can be successfully edited and created
            * vm object is reused
            * template object is reused
            * can only recover a vm in the failure state
            * owner cannot be changed (security)
            * editing user is not granted perms (security)
        """
        url = '/vm/add/'
        args = tuple()
        fail_template = 'ganeti/virtual_machine/create.html'
        success_template = 'ganeti/virtual_machine/create_status.html'

        template = VirtualMachineTemplate()
        template.save()

        # create a failed vm
        failed_vm, cluster2 = self.create_virtual_machine(self.cluster,
                                                          'failed.osuosl.org')
        failed_vm.owner=self.user.get_profile()
        failed_vm.template = template
        failed_vm.save()
        self.vm.rapi.GetJobStatus.response = JOB_RUNNING

        data = dict(cluster=self.cluster.id,
                    start=True,
                    owner=self.user.get_profile().id, #XXX remove this
                    hostname=failed_vm.hostname,
                    disk_template='plain',
                    disk_count=1,
                    disk_size_0=1000,
                    memory=256,
                    vcpus=2,
                    root_path='/',
                    nic_type='paravirtual',
                    disk_type = 'paravirtual',
                    nic_count=1,
                    nic_link_0 = 'br43',
                    nic_mode_0='routed',
                    boot_order='disk',
                    os='image+ubuntu-lucid',
                    pnode=self.cluster.nodes.all()[0],
                    snode=self.cluster.nodes.all()[1])

        errors = [
                    {'hostname': self.vm.hostname}, # attempt to recover vm that hasn't failed
                    {'hostname': failed_vm.hostname, 'owner': self.user1.pk} # attempt to change owner
        ]
        self.assert_view_values(url, args, data, errors, fail_template)


        #noinspection PyUnusedLocal
        def tests(user, response):
            created_vm = VirtualMachine.objects.get(pk=failed_vm.pk)
            self.assertEqual(template.pk, created_vm.template_id)
            self.assertNotEqual(None, created_vm.last_job_id)
        users = [self.superuser]
        self.assert_200(url, args, users, success_template, data=data,
                        method='post', tests=tests, follow=True)


    def test_view_load_recover(self):
        """
        Tests loading a VM that failed to deploy back into the create view
        for editing
        """
        url = '/cluster/%s/%s/recover/'
        args = (self.cluster.slug, self.vm.hostname)

        # vm with no template should redirect
        self.assert_200(url, args, [self.superuser],
                        template='ganeti/virtual_machine/detail.html',
                        follow=True)

        template = VirtualMachineTemplate()
        template.save()
        self.vm.template = template
        self.vm.save()

        self.assert_standard_fails(url, args)
        users = [self.superuser, self.vm_admin, self.vm_modify,
                 self.cluster_admin]
        self.assert_200(url, args, users,
                        template='ganeti/virtual_machine/create.html')
