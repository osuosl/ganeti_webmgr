from django.contrib.auth.models import User, Group
from django.test import TestCase

from ganeti_web import models
from ganeti_web.forms.virtual_machine import NewVirtualMachineForm
from ganeti_web.tests.rapi_proxy import RapiProxy, INFO
from ganeti_web.tests.views.virtual_machine.base import \
    \
    VirtualMachineTestCaseMixin, TestVirtualMachineViewsBase

__all__ = ['TestNewVirtualMachineFormInit',
           'TestNewVirtualMachineFormValidation']

VirtualMachine = models.VirtualMachine
Cluster = models.Cluster

global user, user1, group
global cluster, cluster0, cluster1, cluster2, cluster3


class TestNewVirtualMachineFormInit(TestCase, VirtualMachineTestCaseMixin):

    def setUp(self):
        global user, user1, group, cluster0, cluster1, cluster2, cluster3

        models.client.GanetiRapiClient = RapiProxy
        cluster0 = Cluster.objects.create(hostname='test0', slug='test0')
        cluster1 = Cluster.objects.create(hostname='test1', slug='test1')
        cluster2 = Cluster.objects.create(hostname='test2', slug='test2')
        cluster3 = Cluster.objects.create(hostname='test3', slug='test3')
        cluster0.sync_nodes()
        cluster0.info = INFO

        user = User(id=67, username='tester0')
        user.set_password('secret')
        user.save()
        user1 = User(id=70, username='tester1')
        user1.set_password('secret')
        user1.save()
        group = Group(id=45, name='testing_group')
        group.save()

    def tearDown(self):
        User.objects.all().delete()
        Group.objects.all().delete()
        VirtualMachine.objects.all().delete()
        Cluster.objects.all().delete()

    def test_default_choices(self):
        """
        Test that ChoiceFields have the correct default options
        """
        form = NewVirtualMachineForm(user)
        self.assertEqual([(u'', u'---------')],
            form.fields['nic_type'].choices)
        self.assertEqual([(u'', u'---------'),
            (u'routed', u'routed'),
            (u'bridged', u'bridged')],
            form.fields['nic_mode'].choices)
        self.assertEqual([(u'', u'---------')],
            form.fields['boot_order'].choices)
        self.assertEqual([(u'', u'---------'),
            (u'plain', u'plain'),
            (u'drbd', u'drbd'),
            (u'file', u'file'),
            (u'diskless', u'diskless')],
            form.fields['disk_template'].choices)

    def test_cluster_init(self):
        """
        Tests initializing a form with a Cluster

        Verifies:
            * cluster choices are set correctly
            * node choices are set correctly
        """

        # no cluster
        form = NewVirtualMachineForm(user)
        self.assertEqual([(u'', u'---------')], form.fields['pnode'].choices)
        self.assertEqual([(u'', u'---------')], form.fields['snode'].choices)
        self.assertEqual([(u'', u'---------')], form.fields['os'].choices)

        # cluster from initial data
        form = NewVirtualMachineForm(user, {'cluster':cluster0.id})
        self.assertEqual(set([(u'', u'---------'), (u'gtest1.osuosl.bak', u'gtest1.osuosl.bak'), (u'gtest2.osuosl.bak', u'gtest2.osuosl.bak'), (u'gtest3.osuosl.bak', u'gtest3.osuosl.bak')]), set(form.fields['pnode'].choices))
        self.assertEqual(set([(u'', u'---------'), (u'gtest1.osuosl.bak', u'gtest1.osuosl.bak'), (u'gtest2.osuosl.bak', u'gtest2.osuosl.bak'), (u'gtest3.osuosl.bak', u'gtest3.osuosl.bak')]), set(form.fields['snode'].choices))
        self.assertEqual(form.fields['os'].choices,
            [
                (u'', u'---------'),
                ('Image',
                    [('image+debian-osgeo', 'Debian Osgeo'),
                    ('image+ubuntu-lucid', 'Ubuntu Lucid')]
                )
            ]
        )

        # cluster from initial data
        form = NewVirtualMachineForm(user, {'cluster':cluster0.id})
        self.assertEqual(set([(u'', u'---------'), (u'gtest1.osuosl.bak', u'gtest1.osuosl.bak'), (u'gtest2.osuosl.bak', u'gtest2.osuosl.bak'), (u'gtest3.osuosl.bak', u'gtest3.osuosl.bak')]), set(form.fields['pnode'].choices))
        self.assertEqual(set([(u'', u'---------'), (u'gtest1.osuosl.bak', u'gtest1.osuosl.bak'), (u'gtest2.osuosl.bak', u'gtest2.osuosl.bak'), (u'gtest3.osuosl.bak', u'gtest3.osuosl.bak')]), set(form.fields['snode'].choices))
        self.assertEqual(form.fields['os'].choices,
            [
                (u'', u'---------'),
                ('Image',
                    [('image+debian-osgeo', 'Debian Osgeo'),
                    ('image+ubuntu-lucid', 'Ubuntu Lucid')]
                )
            ]
        )

    def test_cluster_choices_init(self):
        """
        Tests that cluster choices are based on User permissions

        Verifies:
            * superusers have all Clusters as choices
            * if owner is set, only display clusters the owner has permissions
              directly on.  This includes both users and groups
            * if no owner is set, choices include clusters that the user has
              permission directly on, or through a group
        """
        global user

        # no owner, no permissions
        form = NewVirtualMachineForm(user)
        self.assertEqual(set([(u'', u'---------')]), set(form.fields['cluster'].choices))

        # no owner, group and direct permissions
        user.grant('admin', cluster0)
        user.grant('create_vm', cluster1)
        group.grant('admin', cluster2)
        group.user_set.add(user)
        self.assertEqual(set([(u'', u'---------'), (cluster0.pk, u'test0'), (cluster1.pk, u'test1'), (cluster2.pk, u'test2')]), set(form.fields['cluster'].choices))
        user.revoke_all(cluster0)
        user.revoke_all(cluster1)
        group.revoke_all(cluster2)

        # owner, user with no choices
        form = NewVirtualMachineForm(user, initial={'owner':user.get_profile().id})
        self.assertEqual(set([(u'', u'---------')]), set(form.fields['cluster'].choices))

        # owner, user with choices
        user.grant('admin', cluster0)
        user.grant('create_vm', cluster1)
        form = NewVirtualMachineForm(user, initial={'owner':user.get_profile().id})
        self.assertEqual(set([(u'', u'---------'), (cluster0.pk, u'test0'), (cluster1.pk, u'test1')]), set(form.fields['cluster'].choices))

        # owner, group with no choices
        form = NewVirtualMachineForm(user, initial={'owner':group.organization.id})
        self.assertEqual(set([(u'', u'---------')]), set(form.fields['cluster'].choices))

        # owner, group with choices
        group.grant('admin', cluster2)
        group.grant('create_vm', cluster3)
        form = NewVirtualMachineForm(user, initial={'owner':group.organization.id})
        self.assertEqual(set([(u'', u'---------'), (cluster2.pk, u'test2'), (cluster3.pk, u'test3')]), set(form.fields['cluster'].choices))

        # user - superuser
        user.is_superuser = True
        user.save()
        form = NewVirtualMachineForm(user, initial={'owner':user.get_profile().id})
        self.assertEqual(set([(u'', u'---------'), (cluster0.pk, u'test0'), (cluster1.pk, u'test1'), (cluster2.pk, u'test2'), (cluster3.pk, u'test3')]), set(form.fields['cluster'].choices))

        # group - superuser
        form = NewVirtualMachineForm(user, initial={'owner':group.organization.id})
        self.assertEqual(set([(u'', u'---------'), (cluster0.pk, u'test0'), (cluster1.pk, u'test1'), (cluster2.pk, u'test2'), (cluster3.pk, u'test3')]), set(form.fields['cluster'].choices))

    def test_owner_choices_init(self):
        """
        Tests that owner choices are set based on User permissions

        Verifies:
            * superusers have all clusterusers as choices
            * user receives themselves as a choice if they have perms
            * user receives all groups they are a member of
        """

        # user with no choices
        form = NewVirtualMachineForm(user)
        self.assertEqual([(u'', u'---------')], form.fields['owner'].choices)

        # user with perms on self, no groups
        user.grant('admin', cluster0)
        form = NewVirtualMachineForm(user)
        self.assertEqual(
            [
                (u'', u'---------'),
                (user.profile.id, u'tester0'),
            ], form.fields['owner'].choices)
        user.set_perms(['create_vm'], cluster0)
        form = NewVirtualMachineForm(user)
        self.assertEqual(
            [
                (u'', u'---------'),
                (user.profile.id, u'tester0'),
            ], form.fields['owner'].choices)

        # user with perms on self and groups
        group.user_set.add(user)
        group.grant('admin', cluster0)
        form = NewVirtualMachineForm(user)
        self.assertEqual(
            [
                (u'', u'---------'),
                (group.organization.id, u'testing_group'),
                (user.profile.id, u'tester0'),
            ], form.fields['owner'].choices)
        user.revoke_all(cluster0)

        # user with no perms on self, but groups
        form = NewVirtualMachineForm(user)
        self.assertEqual(
            [
                (u'', u'---------'),
                (group.organization.id, u'testing_group'),
            ], form.fields['owner'].choices)
        group.set_perms(['create_vm'], cluster0)
        form = NewVirtualMachineForm(user)
        self.assertEqual(
            [
                (u'', u'---------'),
                (group.organization.id, u'testing_group'),
            ], form.fields['owner'].choices)
        group.revoke_all(cluster0)

        # superuser
        user.is_superuser = True
        user.save()
        form = NewVirtualMachineForm(user)
        self.assertEqual(
            [
                (u'', u'---------'),
                (user.profile.id, u'tester0'),
                (user1.profile.id, u'tester1'),
                (group.organization.id, u'testing_group'),
            ], list(form.fields['owner'].choices))

    def test_default_disks(self):
        user.grant('admin', cluster0)
        form = NewVirtualMachineForm(user)
        self.assertTrue('disk_size_0' in form.fields)
        self.assertFalse('disk_size_1' in form.fields)

    def test_no_disks(self):
        user.grant('admin', cluster0)
        form = NewVirtualMachineForm(user, dict(disk_count=0))
        self.assertFalse('disk_size_0' in form.fields)
        self.assertFalse('disk_size_1' in form.fields)

    def test_single_disk(self):
        user.grant('admin', cluster0)
        form = NewVirtualMachineForm(user, dict(disk_count=1))
        self.assertTrue('disk_size_0' in form.fields)
        self.assertFalse('disk_size_1' in form.fields)

    def test_multiple_disks(self):
        user.grant('admin', cluster0)
        form = NewVirtualMachineForm(user, dict(disk_count=2))
        self.assertTrue('disk_size_0' in form.fields)
        self.assertTrue('disk_size_1' in form.fields)


class TestNewVirtualMachineFormValidation(TestVirtualMachineViewsBase):

    context = globals()

    def setUp(self):
        global cluster
        super(TestNewVirtualMachineFormValidation, self).setUp()
        self.data = dict(cluster=cluster.id,
                        start=True,
                        owner=user.get_profile().id, #XXX remove this
                        hostname='new.vm.hostname',
                        disk_template='plain',
                        disk_count=1,
                        disk_size_0=1000,
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

    def test_invalid_cluster(self):
        """
        An invalid cluster causes a form error.
        """

        data = self.data
        data['cluster'] = -1
        form = NewVirtualMachineForm(user, data)
        self.assertFalse(form.is_valid())

    def test_wrong_cluster(self):
        """
        A cluster the user isn't authorized for causes a form error.
        """

        cluster1 = Cluster(hostname='test2.osuosl.bak', slug='OSL_TEST2')
        cluster1.save()
        data = self.data
        data['cluster'] = cluster.id
        user.grant('create_vm', cluster1)
        user.is_superuser = False
        user.save()
        form = NewVirtualMachineForm(user, data)
        self.assertFalse(form.is_valid())

    def test_required_keys(self):
        """
        If any of these keys are missing from the form data, a form error
        should occur.
        """

        data = self.data

        # grant user.
        user.grant('create_vm', cluster)

        for prop in ['cluster', 'hostname', 'disk_size_0', 'disk_type',
                     'nic_type', 'nic_mode', 'vcpus', 'pnode', 'os',
                     'disk_template', 'boot_order']:
            data_ = data.copy()
            del data_[prop]
            form = NewVirtualMachineForm(user, data_)
            self.assertFalse(form.is_valid(), prop)

    def test_ram_quota_exceeded(self):
        """
        RAM quotas should cause form errors when exceeded.
        """

        data = self.data
        data['memory'] = 2048

        # Login and grant user.
        user.grant('create_vm', cluster)

        cluster.set_quota(user.get_profile(), dict(ram=1000, disk=2000, virtual_cpus=10))
        form = NewVirtualMachineForm(user, data)
        self.assertFalse(form.is_valid())

    def test_data_disk_quota_exceeded(self):
        """
        Disk quotas, when enabled, should cause form errors when exceeded.
        """

        data = self.data
        data['disk_size_0'] = 4000

        # Login and grant user.
        user.grant('create_vm', cluster)
        cluster.set_quota(user.get_profile(), dict(ram=1000, disk=2000, virtual_cpus=10))

        form = NewVirtualMachineForm(user, data)
        self.assertFalse(form.is_valid())

    def test_data_cpu_quota_exceeded(self):
        """
        You may not emulate NUMA systems that exceed your quota.

        XXX should we also test more reasonable CPU limits?
        """

        data = self.data
        data['vcpus'] = 200

        # Login and grant user.
        user.grant('create_vm', cluster)
        cluster.set_quota(user.get_profile(), dict(ram=1000, disk=2000, virtual_cpus=10))

        form = NewVirtualMachineForm(user, data)
        self.assertFalse(form.is_valid())

    def test_invalid_owner(self):
        """
        Obviously bogus owners should cause form errors.
        """
        url = '/vm/add/%s'
        data = self.data
        data['owner'] = -1

        # Login and grant user.
        self.assert_(c.login(username=user.username, password='secret'))
        user.grant('create_vm', cluster)

        form = NewVirtualMachineForm(user, data)
        self.assertFalse(form.is_valid())

    def test_iallocator(self):
        """
        The iallocator should be useable.
        """

        url = '/vm/add/%s'
        data = self.data
        data['iallocator'] = True
        data['iallocator_hostname'] = "hail"

        # Login and grant user.
        user.grant('create_vm', cluster)
        form = NewVirtualMachineForm(user, data)
        self.assertTrue(form.is_valid())

    def test_iallocator_missing(self):
        """
        Enabling the iallocator without actually specifying which iallocator
        to run should cause a form error.
        """

        url = '/vm/add/%s'
        data = self.data
        data['iallocator'] = True

        # Login and grant user.
        user.grant('create_vm', cluster)
        user.get_profile()
        cluster.set_quota(user.get_profile(), dict(ram=1000, disk=2000, virtual_cpus=10))

        user.grant('create_vm', cluster)
        form = NewVirtualMachineForm(user, data)
        self.assertFalse(form.is_valid())