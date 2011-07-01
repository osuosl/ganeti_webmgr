from django.contrib.auth.models import User, Group
from django.test import TestCase

from ganeti_web import models
from ganeti_web.forms.virtual_machine import NewVirtualMachineForm
from ganeti_web.tests.rapi_proxy import RapiProxy, INFO
from ganeti_web.tests.views.virtual_machine.base import VirtualMachineTestCaseMixin

__all__ = ['TestNewVirtualMachineForm']

VirtualMachine = models.VirtualMachine
Cluster = models.Cluster

global user, user1, group
global cluster0, cluster1, cluster2, cluster3


class TestNewVirtualMachineForm(TestCase, VirtualMachineTestCaseMixin):

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



