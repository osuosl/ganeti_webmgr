from django.contrib.auth.models import User, Group

from ganeti_web import models
from ganeti_web.models import VirtualMachineTemplate
from ganeti_web.tests.rapi_proxy import JOB_RUNNING
from ganeti_web.tests.views.virtual_machine.base import TestVirtualMachineViewsBase
from util import client

__all__ = ['TestVirtualMachineCreateView', 'TestVirtualMachineRecoverView']

VirtualMachine = models.VirtualMachine
Cluster = models.Cluster

global user, user1, group, superuser, vm_admin, vm_modify, cluster_admin
global c, cluster, vm


class TestVirtualMachineCreateView(TestVirtualMachineViewsBase):

    context = globals()

    def test_view_create_quota_first_vm(self):
        # XXX seperated from test_view_create_data since it was polluting the environment for later tests
        url = '/vm/add/%s'
        data = dict(cluster=cluster.id,
                    start=True,
                    owner=user.get_profile().id, #XXX remove this
                    hostname='new.vm.hostname',
                    disk_template='plain',
                    disk_size=1000,
                    memory=256,
                    vcpus=2,
                    root_path='/',
                    nic_type='paravirtual',
                    disk_type = 'paravirtual',
                    nic_link = 'br43',
                    nic_mode='routed',
                    boot_order='disk',
                    os='image+ubuntu-lucid',
                    pnode=cluster.nodes.all()[0],
                    snode=cluster.nodes.all()[1])


        # set up for testing quota on user's first VM
        user2 = User(id=43, username='quota_tester')
        user2.set_password('secret')
        user2.grant('create_vm', cluster)
        user2.save()
        #print user2.__dict__
        #print user.__dict__
        profile = user2.get_profile()
        self.assert_(c.login(username=user2.username, password='secret'))

        # POST - over ram quota (user's first VM)
        self.assertEqual(profile.used_resources(cluster), {'ram': 0, 'disk': 0, 'virtual_cpus': 0})
        cluster.set_quota(profile, dict(ram=1000, disk=2000, virtual_cpus=10))
        data_ = data.copy()
        data_['memory'] = 2000
        data_['owner'] = profile.id
        response = c.post(url % '', data_)
        self.assertEqual(200, response.status_code) # 302 if vm creation succeeds
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create.html')
        self.assertFalse(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())

        # POST - over disk quota (user's first WM)
        data_ = data.copy()
        data_['disk_size'] = 9001
        data_['owner'] = profile.id
        response = c.post(url % '', data_)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create.html')
        self.assertFalse(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())

        # POST - over cpu quota (user's first VM)
        data_ = data.copy()
        data_['vcpus'] = 2000
        data_['owner'] = profile.id
        response = c.post(url % '', data_)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create.html')
        self.assertFalse(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())

        # POST - over ram quota (user's first VM) (start = False)
        self.assertEqual(profile.used_resources(cluster), {'ram': 0, 'disk': 0, 'virtual_cpus': 0})
        cluster.set_quota(profile, dict(ram=1000, disk=2000, virtual_cpus=10))
        data_ = data.copy()
        data_['start'] = False
        data_['ram'] = 2000
        data_['owner'] = profile.id
        response = c.post(url % '', data_)
        self.assertEqual(302, response.status_code) # 302 if vm creation succeeds
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTrue(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())
        VirtualMachine.objects.filter(hostname='new.vm.hostname').delete()

        # POST - over disk quota (user's first VM) (start = False)
        data_ = data.copy()
        data_['start'] = False
        data_['disk_size'] = 9001
        data_['owner'] = profile.id
        response = c.post(url % '', data_)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create.html')
        self.assertFalse(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())

        # POST - over cpu quota (user's first VM) (start = False)
        data_ = data.copy()
        data_['start'] = False
        data_['vcpus'] = 2000
        data_['owner'] = profile.id
        response = c.post(url % '', data_)
        self.assertEqual(302, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTrue(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())
        VirtualMachine.objects.filter(hostname='new.vm.hostname').delete()

        # clean up after quota tests
        self.assert_(c.login(username=user.username, password='secret'))

    def test_view_create_data_invalid_cluster(self):
        """
        An invalid cluster causes a form error.
        """

        url = '/vm/add/%s'
        data = dict(cluster=-1,
                    start=True,
                    owner=user.get_profile().id, #XXX remove this
                    hostname='new.vm.hostname',
                    disk_template='plain',
                    disk_size=1000,
                    memory=256,
                    vcpus=2,
                    root_path='/',
                    nic_type='paravirtual',
                    disk_type = 'paravirtual',
                    nic_link = 'br43',
                    nic_mode='routed',
                    boot_order='disk',
                    os='image+ubuntu-lucid',
                    pnode=cluster.nodes.all()[0],
                    snode=cluster.nodes.all()[1])

        self.assert_(c.login(username=user.username, password='secret'))

        user.grant('create_vm', cluster)
        response = c.post(url % '', data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create.html')
        self.assertFalse(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())

    def test_view_create_data_wrong_cluster(self):
        """
        A cluster the user isn't authorized for causes a form error.
        """

        url = '/vm/add/%s'
        cluster1 = Cluster(hostname='test2.osuosl.bak', slug='OSL_TEST2')
        cluster1.save()
        data = dict(cluster=cluster.id,
                    start=True,
                    owner=user.get_profile().id, #XXX remove this
                    hostname='new.vm.hostname',
                    disk_template='plain',
                    disk_size=1000,
                    memory=256,
                    vcpus=2,
                    root_path='/',
                    nic_type='paravirtual',
                    disk_type = 'paravirtual',
                    nic_link = 'br43',
                    nic_mode='routed',
                    boot_order='disk',
                    os='image+ubuntu-lucid',
                    pnode=cluster.nodes.all()[0],
                    snode=cluster.nodes.all()[1])

        self.assert_(c.login(username=user.username, password='secret'))

        user.grant('create_vm', cluster1)
        user.is_superuser = False
        user.save()
        response = c.post(url % '', data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create.html')

    def test_view_create_data_required_keys(self):
        """
        If any of these keys are missing from the form data, a form error
        should occur.
        """

        url = '/vm/add/%s'
        data = dict(cluster=cluster.id,
                    start=True,
                    owner=user.get_profile().id, #XXX remove this
                    hostname='new.vm.hostname',
                    disk_template='plain',
                    disk_size=1000,
                    memory=256,
                    vcpus=2,
                    root_path='/',
                    nic_type='paravirtual',
                    disk_type = 'paravirtual',
                    nic_link = 'br43',
                    nic_mode='routed',
                    boot_order='disk',
                    os='image+ubuntu-lucid',
                    pnode=cluster.nodes.all()[0],
                    snode=cluster.nodes.all()[1])

        # Login and grant user.
        self.assert_(c.login(username=user.username, password='secret'))
        user.grant('create_vm', cluster)

        for prop in ['cluster', 'hostname', 'disk_size', 'disk_type',
                     'nic_type', 'nic_mode', 'vcpus', 'pnode', 'os',
                     'disk_template', 'boot_order']:
            data_ = data.copy()
            del data_[prop]
            response = c.post(url % '', data_)
            self.assertEqual(200, response.status_code)
            self.assertEqual('text/html; charset=utf-8', response['content-type'])
            self.assertTemplateUsed(response, 'ganeti/virtual_machine/create.html')
            self.assertFalse(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())

    def test_view_create_data_ram_quota_exceeded(self):
        """
        RAM quotas should cause form errors when exceeded.
        """

        url = '/vm/add/%s'
        data = dict(cluster=cluster.id,
                    start=True,
                    owner=user.get_profile().id,
                    hostname='new.vm.hostname',
                    disk_template='plain',
                    disk_size=1000,
                    memory=2048,
                    vcpus=2,
                    root_path='/',
                    nic_type='paravirtual',
                    disk_type = 'paravirtual',
                    nic_link = 'br43',
                    nic_mode='routed',
                    boot_order='disk',
                    os='image+ubuntu-lucid',
                    pnode=cluster.nodes.all()[0],
                    snode=cluster.nodes.all()[1])

        # Login and grant user.
        self.assert_(c.login(username=user.username, password='secret'))
        user.grant('create_vm', cluster)

        cluster.set_quota(user.get_profile(), dict(ram=1000, disk=2000, virtual_cpus=10))
        response = c.post(url % '', data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create.html')
        self.assertFalse(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())

    def test_view_create_data_disk_quota_exceeded(self):
        """
        Disk quotas, when enabled, should cause form errors when exceeded.
        """

        url = '/vm/add/%s'
        data = dict(cluster=cluster.id,
                    start=True,
                    owner=user.get_profile().id,
                    hostname='new.vm.hostname',
                    disk_template='plain',
                    disk_size=4000,
                    memory=256,
                    vcpus=2,
                    root_path='/',
                    nic_type='paravirtual',
                    disk_type = 'paravirtual',
                    nic_link = 'br43',
                    nic_mode='routed',
                    boot_order='disk',
                    os='image+ubuntu-lucid',
                    pnode=cluster.nodes.all()[0],
                    snode=cluster.nodes.all()[1])

        # Login and grant user.
        self.assert_(c.login(username=user.username, password='secret'))
        user.grant('create_vm', cluster)
        cluster.set_quota(user.get_profile(), dict(ram=1000, disk=2000, virtual_cpus=10))

        response = c.post(url % '', data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create.html')
        self.assertFalse(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())

    def test_view_create_data_cpu_quota_exceeded(self):
        """
        You may not emulate NUMA systems that exceed your quota.

        XXX should we also test more reasonable CPU limits?
        """

        url = '/vm/add/%s'
        data = dict(cluster=cluster.id,
                    start=True,
                    owner=user.get_profile().id,
                    hostname='new.vm.hostname',
                    disk_template='plain',
                    disk_size=1000,
                    memory=256,
                    vcpus=200,
                    root_path='/',
                    nic_type='paravirtual',
                    disk_type = 'paravirtual',
                    nic_link = 'br43',
                    nic_mode='routed',
                    boot_order='disk',
                    os='image+ubuntu-lucid',
                    pnode=cluster.nodes.all()[0],
                    snode=cluster.nodes.all()[1])

        # Login and grant user.
        self.assert_(c.login(username=user.username, password='secret'))
        user.grant('create_vm', cluster)
        cluster.set_quota(user.get_profile(), dict(ram=1000, disk=2000, virtual_cpus=10))

        response = c.post(url % '', data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create.html')
        self.assertFalse(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())

    def test_view_create_data_invalid_owner(self):
        """
        Obviously bogus owners should cause form errors.
        """

        url = '/vm/add/%s'
        data = dict(cluster=cluster.id,
                    start=True,
                    owner=-1,
                    hostname='new.vm.hostname',
                    disk_template='plain',
                    disk_size=1000,
                    memory=256,
                    vcpus=2,
                    root_path='/',
                    nic_type='paravirtual',
                    disk_type = 'paravirtual',
                    nic_link = 'br43',
                    nic_mode='routed',
                    boot_order='disk',
                    os='image+ubuntu-lucid',
                    pnode=cluster.nodes.all()[0],
                    snode=cluster.nodes.all()[1])

        # Login and grant user.
        self.assert_(c.login(username=user.username, password='secret'))
        user.grant('create_vm', cluster)

        response = c.post(url % '', data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create.html')
        self.assertFalse(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())

    def test_view_create_data_iallocator(self):
        """
        The iallocator should be useable.
        """

        url = '/vm/add/%s'
        data = dict(cluster=cluster.id,
                    start=True,
                    owner=user.get_profile().id, #XXX remove this
                    hostname='new.vm.hostname',
                    disk_template='plain',
                    disk_size=1000,
                    memory=256,
                    vcpus=2,
                    root_path='/',
                    nic_type='paravirtual',
                    disk_type = 'paravirtual',
                    nic_link = 'br43',
                    nic_mode='routed',
                    boot_order='disk',
                    os='image+ubuntu-lucid',
                    iallocator=True,
                    iallocator_hostname="hail")

        # Login and grant user.
        self.assert_(c.login(username=user.username, password='secret'))
        user.grant('create_vm', cluster)

        response = c.post(url % '', data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create_status.html')
        new_vm = VirtualMachine.objects.get(hostname='new.vm.hostname')
        self.assertTrue(user.has_perm('admin', new_vm))

    def test_view_create_data_iallocator_missing(self):
        """
        Enabling the iallocator without actually specifying which iallocator
        to run should cause a form error.
        """

        url = '/vm/add/%s'
        data = dict(cluster=cluster.id,
                    start=True,
                    owner=user.get_profile().id, #XXX remove this
                    hostname='new.vm.hostname',
                    disk_template='plain',
                    disk_size=1000,
                    memory=256,
                    vcpus=2,
                    root_path='/',
                    nic_type='paravirtual',
                    disk_type = 'paravirtual',
                    nic_link = 'br43',
                    nic_mode='routed',
                    boot_order='disk',
                    os='image+ubuntu-lucid',
                    pnode=cluster.nodes.all()[0],
                    snode=cluster.nodes.all()[1],
                    iallocator=True)

        # Login and grant user.
        self.assert_(c.login(username=user.username, password='secret'))
        user.grant('create_vm', cluster)
        user.get_profile()
        cluster.set_quota(user.get_profile(), dict(ram=1000, disk=2000, virtual_cpus=10))

        user.grant('create_vm', cluster)
        response = c.post(url % '', data)
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
        data = dict(cluster=cluster.id,
                    start=True,
                    owner=user.get_profile().id, #XXX remove this
                    hostname='new.vm.hostname',
                    disk_template='plain',
                    disk_size=1000,
                    memory=256,
                    vcpus=2,
                    root_path='/',
                    nic_type='paravirtual',
                    disk_type = 'paravirtual',
                    nic_link = 'br43',
                    nic_mode='routed',
                    boot_order='disk',
                    os='image+ubuntu-lucid',
                    pnode=cluster.nodes.all()[0],
                    snode=cluster.nodes.all()[1])

        # Login and grant user.
        self.assert_(c.login(username=user.username, password='secret'))
        user.grant('create_vm', cluster)
        cluster.set_quota(user.get_profile(), dict(ram=1000, disk=2000, virtual_cpus=10))

        # POST - user authorized for cluster (create_vm)
        user.grant('create_vm', cluster)
        data_ = data.copy()
        self.assertFalse(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())
        response = c.post(url % '', data_, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create_status.html')
        new_vm = VirtualMachine.objects.get(hostname='new.vm.hostname')
        self.assertEqual(new_vm, response.context['instance'])
        self.assert_(user.has_perm('admin', new_vm))
        user.revoke_all(cluster)
        user.revoke_all(new_vm)
        VirtualMachine.objects.all().delete()

        # POST - user authorized for cluster (admin)
        user.grant('admin', cluster)
        response = c.post(url % '', data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create_status.html')
        new_vm = VirtualMachine.objects.get(hostname='new.vm.hostname')
        self.assertEqual(new_vm, response.context['instance'])
        self.assert_(user.has_perm('admin', new_vm))
        VirtualMachine.objects.all().delete()
        user.revoke_all(cluster)
        user.revoke_all(new_vm)

        # POST - User attempting to be other user
        user.grant('admin', cluster)
        data_ = data.copy()
        data_['owner'] = user1.get_profile().id
        response = c.post(url % '', data_)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create.html')
        self.assertFalse(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())
        user.revoke_all(cluster)

        # POST - user authorized for cluster (superuser)
        user.is_superuser = True
        user.save()
        response = c.post(url % '', data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create_status.html')
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
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create.html')
        self.assertFalse(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())
        cluster.rapi.CreateInstance.error = None

        # POST - User attempting to be other user (superuser)
        data_ = data.copy()
        data_['owner'] = user1.get_profile().id
        response = c.post(url % '', data_, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create_status.html')
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
        user.grant('admin', cluster)
        group.grant('create_vm', cluster)
        self.assertFalse(group in user.groups.all())
        response = c.post(url % '', data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create.html')
        self.assertFalse(VirtualMachine.objects.filter(hostname='new.vm.hostname').exists())
        user.revoke_all(cluster)
        group.revoke_all(cluster)
        VirtualMachine.objects.all().delete()

        # add user to group
        group.user_set.add(user)

        # POST - group authorized for cluster (create_vm)
        group.grant('create_vm', cluster)
        response = c.post(url % '', data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create_status.html')
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
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create_status.html')
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
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create_status.html')
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
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create_status.html')
        new_vm = VirtualMachine.objects.get(hostname='new.vm.hostname')
        self.assertEqual(new_vm, response.context['instance'])
        self.assert_(group1.has_perm('admin', new_vm))
        self.assertFalse(group.has_perm('admin', new_vm))

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
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create.html')
        user.revoke_all(cluster)

        # authorized GET (cluster admin permissions)
        user.grant('admin', cluster)
        response = c.get(url % '')
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create.html')
        user.revoke_all(cluster)

        # authorized GET (superuser)
        user.is_superuser = True
        user.save()
        response = c.get(url % '')
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create.html')

        # GET unknown cluster
        response = c.get(url % 'DOES_NOT_EXIST')
        self.assertEqual(404, response.status_code)

        # GET valid cluster
        response = c.get(url % cluster.slug)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'ganeti/virtual_machine/create.html')


class TestVirtualMachineRecoverView(TestVirtualMachineViewsBase):

    context = globals()

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
        failed_vm, cluster2 = self.create_virtual_machine(cluster, 'failed.osuosl.org')
        failed_vm.owner=user.get_profile()
        failed_vm.template = template
        failed_vm.save()
        vm.rapi.GetJobStatus.response = JOB_RUNNING

        data = dict(cluster=cluster.id,
                    start=True,
                    owner=user.get_profile().id, #XXX remove this
                    hostname=failed_vm.hostname,
                    disk_template='plain',
                    disk_size=1000,
                    memory=256,
                    vcpus=2,
                    root_path='/',
                    nic_type='paravirtual',
                    disk_type = 'paravirtual',
                    nic_link = 'br43',
                    nic_mode='routed',
                    boot_order='disk',
                    os='image+ubuntu-lucid',
                    pnode=cluster.nodes.all()[0],
                    snode=cluster.nodes.all()[1])

        errors = [
                    {'hostname':vm.hostname}, # attempt to recover vm that hasn't failed
                    {'hostname':failed_vm.hostname, 'owner':user1.pk} # attempt to change owner
        ]
        self.assert_view_values(url, args, data, errors, fail_template)

        
        #noinspection PyUnusedLocal
        def tests(user, response):
            created_vm = VirtualMachine.objects.get(pk=failed_vm.pk)
            self.assertEqual(template.pk, created_vm.template_id)
            self.assertNotEqual(None, created_vm.last_job_id)
        users = [superuser]
        self.assert_200(url, args, users, success_template, data=data, method='post', tests=tests, follow=True)


    def test_view_load_recover(self):
        """
        Tests loading a VM that failed to deploy back into the create view
        for editing
        """
        url = '/cluster/%s/%s/recover/'
        args = (cluster.slug, vm.hostname)

        # vm with no template should redirect
        self.assert_200(url, args, [superuser], template='ganeti/virtual_machine/detail.html', follow=True)

        template = VirtualMachineTemplate()
        template.save()
        vm.template = template
        vm.save()

        self.assert_standard_fails(url, args)
        users = [superuser, vm_admin, vm_modify, cluster_admin]
        self.assert_200(url, args, users, template='ganeti/virtual_machine/create.html')
