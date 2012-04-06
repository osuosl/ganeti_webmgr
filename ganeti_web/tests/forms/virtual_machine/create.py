from django.contrib.auth.models import User, Group
from django.test import TestCase

from ganeti_web import models
from ganeti_web.forms.virtual_machine import NewVirtualMachineForm
from ganeti_web.util.rapi_proxy import RapiProxy, INFO
from ganeti_web.tests.views.virtual_machine.base import (
    VirtualMachineTestCaseMixin, TestVirtualMachineViewsBase)

__all__ = ['TestNewVirtualMachineFormInit',
           'TestNewVirtualMachineFormValidation']

VirtualMachine = models.VirtualMachine
Cluster = models.Cluster


class TestNewVirtualMachineFormInit(TestCase, VirtualMachineTestCaseMixin):

    def setUp(self):
        self.user = User(id=67, username='tester0')
        self.user.set_password('secret')
        self.user.save()
        self.user1 = User(id=70, username='tester1')
        self.user1.set_password('secret')
        self.user1.save()
        self.group = Group(id=45, name='testing_group')
        self.group.save()

        models.client.GanetiRapiClient = RapiProxy
        self.cluster0 = Cluster.objects.create(hostname='test0', slug='test0')
        self.cluster1 = Cluster.objects.create(hostname='test1', slug='test1')
        self.cluster2 = Cluster.objects.create(hostname='test2', slug='test2')
        self.cluster3 = Cluster.objects.create(hostname='test3', slug='test3')
        self.cluster0.sync_nodes()

        # Give each cluster write permissions, and set it's info
        for cluster in (self.cluster0, self.cluster1, self.cluster2,
                        self.cluster3):
            cluster.username = self.user.username
            cluster.password = 'foobar'
            cluster.info = INFO
            cluster.save()

    def tearDown(self):
        User.objects.all().delete()
        Group.objects.all().delete()
        VirtualMachine.objects.all().delete()
        Cluster.objects.all().delete()

    def test_default_choices(self):
        """
        Test that ChoiceFields have the correct default options
        """
        form = NewVirtualMachineForm(self.user)
        self.assertEqual([(u'', u'---------')],
            form.fields['nic_type'].choices)
        self.assertEqual([(u'', u'---------'),
            (u'routed', u'routed'),
            (u'bridged', u'bridged')],
            form.fields['nic_mode_0'].choices)
        self.assertEqual([(u'', u'---------')],
            form.fields['boot_order'].choices)
        self.assertEqual([(u'', u'---------'),
            (u'plain', u'plain'),
            (u'drbd', u'drbd'),
            (u'file', u'file'),
            (u'diskless', u'diskless')],
            form.fields['disk_template'].choices)

    def test_init_and_data_params(self):
        """
        Tests that passing initial does not trigger validation

        Verifies:
            * Passing data (arg[0]) will trigger validation
            * Passing initial will not trigger validation
        """
        form = NewVirtualMachineForm(self.user, initial={})
        self.assertEqual({}, form.errors)

        form = NewVirtualMachineForm(self.user, {})
        self.assertNotEqual({}, form.errors)

    def test_cluster_init(self):
        """
        Tests initializing a form with a Cluster

        Verifies:
            * cluster choices are set correctly
            * node choices are set correctly
        """

        # no cluster
        form = NewVirtualMachineForm(self.user)
        self.assertEqual([(u'', u'---------')], form.fields['pnode'].choices)
        self.assertEqual([(u'', u'---------')], form.fields['snode'].choices)
        self.assertEqual([(u'', u'---------')], form.fields['os'].choices)

        # cluster from initial data
        form = NewVirtualMachineForm(self.user, {'cluster': self.cluster0.id})
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
        form = NewVirtualMachineForm(self.user, {'cluster':self.cluster0.id})
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

        # no owner, no permissions
        form = NewVirtualMachineForm(self.user)
        self.assertEqual(set([(u'', u'---------')]), set(form.fields['cluster'].choices))

        # no owner, group and direct permissions
        self.user.grant('admin', self.cluster0)
        self.user.grant('create_vm', self.cluster1)
        self.group.grant('admin', self.cluster2)
        self.group.user_set.add(self.user)
        self.assertEqual(set([(u'', u'---------'), (self.cluster0.pk, u'test0'), (self.cluster1.pk, u'test1'), (self.cluster2.pk, u'test2')]), set(form.fields['cluster'].choices))
        self.user.revoke_all(self.cluster0)
        self.user.revoke_all(self.cluster1)
        self.group.revoke_all(self.cluster2)

        # owner, user with no choices
        form = NewVirtualMachineForm(self.user, initial={'owner':self.user.get_profile().id})
        self.assertEqual(set([(u'', u'---------')]), set(form.fields['cluster'].choices))

        # owner, user with choices
        self.user.grant('admin', self.cluster0)
        self.user.grant('create_vm', self.cluster1)
        form = NewVirtualMachineForm(self.user, initial={'owner':self.user.get_profile().id})
        self.assertEqual(set([(u'', u'---------'), (self.cluster0.pk, u'test0'), (self.cluster1.pk, u'test1')]), set(form.fields['cluster'].choices))

        # owner, group with no choices
        form = NewVirtualMachineForm(self.user, initial={'owner':self.group.organization.id})
        self.assertEqual(set([(u'', u'---------')]), set(form.fields['cluster'].choices))

        # owner, group with choices
        self.group.grant('admin', self.cluster2)
        self.group.grant('create_vm', self.cluster3)
        form = NewVirtualMachineForm(self.user, initial={'owner':self.group.organization.id})
        self.assertEqual(set([(u'', u'---------'), (self.cluster2.pk, u'test2'), (self.cluster3.pk, u'test3')]), set(form.fields['cluster'].choices))

        # user - superuser
        self.user.is_superuser = True
        self.user.save()
        form = NewVirtualMachineForm(self.user, initial={'owner':self.user.get_profile().id})
        self.assertEqual(set([(u'', u'---------'), (self.cluster0.pk, u'test0'), (self.cluster1.pk, u'test1'), (self.cluster2.pk, u'test2'), (self.cluster3.pk, u'test3')]), set(form.fields['cluster'].choices))

        # group - superuser
        form = NewVirtualMachineForm(self.user, initial={'owner':self.group.organization.id})
        self.assertEqual(set([(u'', u'---------'), (self.cluster0.pk, u'test0'), (self.cluster1.pk, u'test1'), (self.cluster2.pk, u'test2'), (self.cluster3.pk, u'test3')]), set(form.fields['cluster'].choices))

    def test_owner_choices_init(self):
        """
        Tests that owner choices are set based on User permissions

        Verifies:
            * superusers have all clusterusers as choices
            * user receives themselves as a choice if they have perms
            * user receives all groups they are a member of
        """

        # user with no choices
        form = NewVirtualMachineForm(self.user)
        self.assertEqual([(u'', u'---------')], form.fields['owner'].choices)

        # user with perms on self, no groups
        self.user.grant('admin', self.cluster0)
        form = NewVirtualMachineForm(self.user)
        self.assertEqual(
            [
                (u'', u'---------'),
                (self.user.profile.id, u'tester0'),
            ], form.fields['owner'].choices)
        self.user.set_perms(['create_vm'], self.cluster0)
        form = NewVirtualMachineForm(self.user)
        self.assertEqual(
            [
                (u'', u'---------'),
                (self.user.profile.id, u'tester0'),
            ], form.fields['owner'].choices)

        # user with perms on self and groups
        self.group.user_set.add(self.user)
        self.group.grant('admin', self.cluster0)
        form = NewVirtualMachineForm(self.user)
        self.assertEqual(
            [
                (u'', u'---------'),
                (self.group.organization.id, u'testing_group'),
                (self.user.profile.id, u'tester0'),
            ], form.fields['owner'].choices)
        self.user.revoke_all(self.cluster0)

        # user with no perms on self, but groups
        form = NewVirtualMachineForm(self.user)
        self.assertEqual(
            [
                (u'', u'---------'),
                (self.group.organization.id, u'testing_group'),
            ], form.fields['owner'].choices)
        self.group.set_perms(['create_vm'], self.cluster0)
        form = NewVirtualMachineForm(self.user)
        self.assertEqual(
            [
                (u'', u'---------'),
                (self.group.organization.id, u'testing_group'),
            ], form.fields['owner'].choices)
        self.group.revoke_all(self.cluster0)

        # superuser
        self.user.is_superuser = True
        self.user.save()
        form = NewVirtualMachineForm(self.user)
        self.assertEqual(
            [
                (u'', u'---------'),
                (self.user.profile.id, u'tester0'),
                (self.user1.profile.id, u'tester1'),
                (self.group.organization.id, u'testing_group'),
            ], list(form.fields['owner'].choices))

    def test_default_disks(self):
        self.user.grant('admin', self.cluster0)
        form = NewVirtualMachineForm(self.user)
        self.assertTrue('disk_size_0' in form.fields)
        self.assertFalse('disk_size_1' in form.fields)

    def test_no_disks(self):
        self.user.grant('admin', self.cluster0)
        form = NewVirtualMachineForm(self.user, dict(disk_count=0))
        self.assertFalse('disk_size_0' in form.fields)
        self.assertFalse('disk_size_1' in form.fields)

    def test_single_disk(self):
        self.user.grant('admin', self.cluster0)
        form = NewVirtualMachineForm(self.user, dict(disk_count=1))
        self.assertTrue('disk_size_0' in form.fields)
        self.assertFalse('disk_size_1' in form.fields)

    def test_multiple_disks(self):
        self.user.grant('admin', self.cluster0)
        form = NewVirtualMachineForm(self.user, dict(disk_count=2))
        self.assertTrue('disk_size_0' in form.fields)
        self.assertTrue('disk_size_1' in form.fields)

    def test_multiple_disks_from_dict(self):
        self.user.grant('admin', self.cluster0)
        initial = dict(disks=[dict(size=123), dict(size=456)])
        form = NewVirtualMachineForm(self.user, initial)
        self.assertTrue('disk_size_0' in form.fields)
        self.assertTrue('disk_size_1' in form.fields)
        
        data = form.data
        self.assertEqual(2, data['disk_count'])
        self.assertEqual(123, data['disk_size_0'])
        self.assertEqual(456, data['disk_size_1'])

    def test_default_nics(self):
        self.user.grant('admin', self.cluster0)
        form = NewVirtualMachineForm(self.user)
        self.assertTrue('nic_mode_0' in form.fields)
        self.assertFalse('nic_mode_1' in form.fields)
        self.assertTrue('nic_link_0' in form.fields)
        self.assertFalse('nic_link_1' in form.fields)

    def test_no_nics(self):
        self.user.grant('admin', self.cluster0)
        form = NewVirtualMachineForm(self.user, dict(nic_count=0))
        self.assertFalse('nic_mode_0' in form.fields)
        self.assertFalse('nic_mode_1' in form.fields)
        self.assertFalse('nic_link_0' in form.fields)
        self.assertFalse('nic_link_1' in form.fields)

    def test_single_nic(self):
        self.user.grant('admin', self.cluster0)
        form = NewVirtualMachineForm(self.user, dict(nic_count=1))
        self.assertTrue('nic_mode_0' in form.fields)
        self.assertFalse('nic_mode_1' in form.fields)
        self.assertTrue('nic_link_0' in form.fields)
        self.assertFalse('nic_link_1' in form.fields)

    def test_multiple_nics(self):
        self.user.grant('admin', self.cluster0)
        form = NewVirtualMachineForm(self.user, dict(nic_count=2))
        self.assertTrue('nic_mode_0' in form.fields)
        self.assertTrue('nic_mode_1' in form.fields)
        self.assertTrue('nic_link_0' in form.fields)
        self.assertTrue('nic_link_1' in form.fields)

    def test_multiple_nics_from_dict(self):
        self.user.grant('admin', self.cluster0)
        initial = dict(nics=[dict(mode=123, link='br0'), dict(mode=456, link='br1')])
        form = NewVirtualMachineForm(self.user, initial)
        self.assertTrue('nic_mode_0' in form.fields)
        self.assertTrue('nic_mode_1' in form.fields)
        self.assertTrue('nic_link_0' in form.fields)
        self.assertTrue('nic_link_1' in form.fields)

        data = form.data
        self.assertEqual(2, data['nic_count'])
        self.assertEqual(123, data['nic_mode_0'])
        self.assertEqual(456, data['nic_mode_1'])
        self.assertEqual('br0', data['nic_link_0'])
        self.assertEqual('br1', data['nic_link_1'])


class TestNewVirtualMachineFormValidation(TestVirtualMachineViewsBase):

    def setUp(self):
        super(TestNewVirtualMachineFormValidation, self).setUp()
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

    def test_invalid_cluster(self):
        """
        An invalid cluster causes a form error.
        """

        data = self.data
        data['cluster'] = -1
        form = NewVirtualMachineForm(self.user, data)
        self.assertFalse(form.is_valid())

    def test_wrong_cluster(self):
        """
        A cluster the user isn't authorized for causes a form error.
        """

        self.cluster1 = Cluster(hostname='test2.osuosl.bak', slug='OSL_TEST2')
        self.cluster1.save()
        data = self.data
        data['cluster'] = self.cluster.id
        self.user.grant('create_vm', self.cluster1)
        self.user.is_superuser = False
        self.user.save()
        form = NewVirtualMachineForm(self.user, data)
        self.assertFalse(form.is_valid())

    def test_required_keys(self):
        """
        If any of these keys are missing from the form data, a form error
        should occur.
        """

        data = self.data

        # grant user.
        self.user.grant('create_vm', self.cluster)

        for prop in ['cluster', 'hostname', 'disk_size_0', 'disk_type',
                     'nic_type', 'nic_mode_0', 'vcpus', 'pnode', 'os',
                     'disk_template', 'boot_order']:
            data_ = data.copy()
            del data_[prop]
            form = NewVirtualMachineForm(self.user, data_)
            self.assertFalse(form.is_valid(), prop)

    def test_ram_quota_exceeded(self):
        """
        RAM quotas should cause form errors when exceeded.
        """

        data = self.data
        data['memory'] = 2048

        # Login and grant user.
        self.user.grant('create_vm', self.cluster)

        self.cluster.set_quota(self.user.get_profile(), dict(ram=1000, disk=2000, virtual_cpus=10))
        form = NewVirtualMachineForm(self.user, data)
        self.assertFalse(form.is_valid())

    def test_data_disk_quota_exceeded(self):
        """
        Disk quotas, when enabled, should cause form errors when exceeded.
        """

        data = self.data
        data['disk_size_0'] = 4000

        # Login and grant user.
        self.user.grant('create_vm', self.cluster)
        self.cluster.set_quota(self.user.get_profile(), dict(ram=1000, disk=2000, virtual_cpus=10))

        form = NewVirtualMachineForm(self.user, data)
        self.assertFalse(form.is_valid())

    def test_data_cpu_quota_exceeded(self):
        """
        You may not emulate NUMA systems that exceed your quota.

        XXX should we also test more reasonable CPU limits?
        """

        data = self.data
        data['vcpus'] = 200

        # Login and grant user.
        self.user.grant('create_vm', self.cluster)
        self.cluster.set_quota(self.user.get_profile(), dict(ram=1000, disk=2000, virtual_cpus=10))

        form = NewVirtualMachineForm(self.user, data)
        self.assertFalse(form.is_valid())

    def test_invalid_owner(self):
        """
        Obviously bogus owners should cause form errors.
        """
        url = '/vm/add/%s'
        data = self.data
        data['owner'] = -1

        # Login and grant user.
        self.assertTrue(self.c.login(username=self.user.username, password='secret'))
        self.user.grant('create_vm', self.cluster)

        form = NewVirtualMachineForm(self.user, data)
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
        self.user.grant('create_vm', self.cluster)
        form = NewVirtualMachineForm(self.user, data)
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
        self.user.grant('create_vm', self.cluster)
        self.user.get_profile()
        self.cluster.set_quota(self.user.get_profile(), dict(ram=1000, disk=2000, virtual_cpus=10))

        self.user.grant('create_vm', self.cluster)
        form = NewVirtualMachineForm(self.user, data)
        self.assertFalse(form.is_valid())

    def test_no_disks(self):
        """
        test that diskless allows no disks
        """
        self.data['disk_count'] = 0
        self.user.grant('create_vm', self.cluster)
        form = NewVirtualMachineForm(self.user, self.data)
        self.assertTrue(form.is_valid())

    def test_multiple_disks_missing_size(self):
        """
        tests submitting multiple disks, and that one is missing disk_size
        """
        self.data['disk_count'] = 2
        self.user.grant('create_vm', self.cluster)
        form = NewVirtualMachineForm(self.user, self.data)
        self.assertFalse(form.is_valid())

    def test_multiple_disks_disk_size_calculation(self):
        """
        test that multiple disks are used in calculating total disk size
        """
        self.data['disk_count'] = 2
        self.data['disk_size_1'] = 3836
        self.user.grant('create_vm', self.cluster)
        form = NewVirtualMachineForm(self.user, self.data)
        self.assertTrue(form.is_valid())
        self.assertEqual(4836, form.cleaned_data['disk_size'])

    def test_no_nics(self):
        """
        test vm with no networking
        """
        self.data['nic_count'] = 0
        self.user.grant('create_vm', self.cluster)
        form = NewVirtualMachineForm(self.user, self.data)
        self.assertTrue(form.is_valid())

    def test_multiple_nics_missing_nic_link(self):
        """
        tests submitting multiple nics, and that one is missing nic_link
        """
        self.data['nic_count'] = 2
        self.data['nic_mode_0'] = 'br0'
        self.data['nic_mode_1'] = 'br1'
        self.user.grant('create_vm', self.cluster)
        form = NewVirtualMachineForm(self.user, self.data)
        self.assertFalse(form.is_valid())

    def test_multiple_nics_missing_nic_mode(self):
        """
        tests submitting multiple nics, and that one is missing nic_mode
        """
        self.data['nic_count'] = 2
        self.data['nic_link_0'] = 'br0'
        self.data['nic_link_1'] = 'br1'
        self.user.grant('create_vm', self.cluster)
        form = NewVirtualMachineForm(self.user, self.data)
        self.assertFalse(form.is_valid())
