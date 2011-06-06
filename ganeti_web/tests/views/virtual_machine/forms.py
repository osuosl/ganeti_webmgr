from itertools import chain
import unittest

from django.contrib.auth.models import User, Group
from django.test import TestCase

from ganeti_web import models
from ganeti_web import constants
from ganeti_web.forms.virtual_machine import NewVirtualMachineForm, \
    HvmModifyVirtualMachineForm, KvmModifyVirtualMachineForm, \
    PvmModifyVirtualMachineForm
from ganeti_web.tests.rapi_proxy import RapiProxy, XenRapiProxy, INFO, XEN_INFO
from ganeti_web.tests.views.virtual_machine.base import VirtualMachineTestCaseMixin

__all__ = ['TestNewVirtualMachineForm',
    'TestKvmModifyVirtualMachineForm',
    'TestHvmModifyVirtualMachineForm',
    'TestPvmModifyVirtualMachineForm']

VirtualMachine = models.VirtualMachine
Cluster = models.Cluster

global user, user1, group
global cluster0, cluster1, cluster2, cluster3
global kvm_cluster, hvm_cluster, pvm_cluster
global kvm_vm, hvm_vm, pvm_vm

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


class TestKvmModifyVirtualMachineForm(TestCase, VirtualMachineTestCaseMixin):
    def setUp(self):
        global kvm_cluster, kvm_vm

        models.client.GanetiRapiClient = RapiProxy
        kvm_cluster = Cluster.objects.create(hostname='test0.kvm_cluster',
            slug='test0')
        kvm_vm = VirtualMachine.objects.create(hostname='kvm.osuosl',
            cluster=kvm_cluster)

    def tearDown(self):
        VirtualMachine.objects.all().delete()
        Cluster.objects.all().delete()

    def test_meta_rapiproxy_set(self):
        self.assertEqual(models.client.GanetiRapiClient, RapiProxy)

    def test_form_defaults(self):
        """
        Test the default choices for ChoiceFields on the form.
        """
        choices = constants.KVM_CHOICES
        disk_type = choices['disk_type']
        nic_type = choices['nic_type']
        boot_order = choices['boot_order']
        disk_caches = constants.HV_DISK_CACHES
        kvm_flags = constants.KVM_FLAGS
        security_models = constants.HV_SECURITY_MODELS
        usb_mice = constants.HV_USB_MICE

        form = KvmModifyVirtualMachineForm(kvm_vm)
        fields = form.fields
        self.assertEqual(set(disk_type),
            set(fields['disk_type'].choices))
        self.assertEqual(set(nic_type),
            set(fields['nic_type'].choices))
        self.assertEqual(set(boot_order),
            set(fields['boot_order'].choices))
        self.assertEqual(set(disk_caches),
            set(fields['disk_cache'].choices))
        self.assertEqual(set(kvm_flags),
            set(fields['kvm_flag'].choices))
        self.assertEqual(set(security_models),
            set(fields['security_model'].choices))
        self.assertEqual(set(usb_mice),
            set(fields['usb_mouse'].choices))

    def test_initial_form_fields(self):
        """
        Test that the form does not contain any extra fields.
        """
        modify_fields = ('vcpus', 'memory', 'nic_link', 'nic_mac', 'os_name')
        hv_fields = KvmModifyVirtualMachineForm.hvparam_fields
        form = KvmModifyVirtualMachineForm(kvm_vm)

        for field in chain(modify_fields, hv_fields):
            self.assertTrue(field in form.fields)

        for field in form.Meta.exclude:
            self.assertFalse(field in form.fields)


class TestHvmModifyVirtualMachineForm(TestCase, VirtualMachineTestCaseMixin):
    def setUp(self):
        from ganeti_web.tests.rapi_proxy import XEN_HVM_INSTANCE
        global hvm_cluster, hvm_vm

        models.client.GanetiRapiClient = XenRapiProxy
        hvm_cluster = Cluster.objects.create(hostname='test2.hvm_cluster',
            slug='test2')
        hvm_cluster.info = XEN_INFO.copy()
        hvm_cluster.info['default_hypervisor'] = 'xen-hvm'
        hvm_vm = VirtualMachine.objects.create(hostname='hvm.osuosl',
            cluster=hvm_cluster)
        hvm_vm.info = XEN_HVM_INSTANCE

    def tearDown(self):
        User.objects.all().delete()
        Group.objects.all().delete()
        VirtualMachine.objects.all().delete()
        Cluster.objects.all().delete()

    def test_meta_xenrapiproxy_set(self):
        self.assertEqual(models.client.GanetiRapiClient, XenRapiProxy)

    def test_meta_default_hypervisor(self):
        self.assertEqual(hvm_cluster.info['default_hypervisor'], 'xen-hvm')

    def test_form_defaults(self):
        choices = constants.HVM_CHOICES
        disk_type = choices['disk_type']
        nic_type = choices['nic_type']
        boot_order = choices['boot_order']

        form = HvmModifyVirtualMachineForm(hvm_vm)
        self.assertEqual(set(disk_type),
            set(form.fields['disk_type'].choices))
        self.assertEqual(set(nic_type),
            set(form.fields['nic_type'].choices))
        self.assertEqual(set(boot_order),
            set(form.fields['boot_order'].choices))

    def test_initial_form_fields(self):
        """
        Test that the form does not contain any extra fields.
        """
        modify_fields = ('vcpus', 'memory', 'nic_link', 'nic_mac', 'os_name')
        hv_fields = HvmModifyVirtualMachineForm.hvparam_fields
        form = HvmModifyVirtualMachineForm(hvm_vm)

        for field in chain(modify_fields, hv_fields):
            self.assertTrue(field in form.fields)

        for field in form.Meta.exclude:
            self.assertFalse(field in form.fields)
        """
        # Uncomment to see if modify contains all available hvparam fields
        hvparam_fields = HvmModifyVirtualMachineForm.hvparam_fields
        hvparams = hvm_cluster.info['hvparams']['xen-hvm']
        self.assertEqual(set(hvparams), set(hvparam_fields))
        """

    def test_field_initial_values(self):
        """
        Test that fields contain the correct initial values taken from a vm.
        """
        hvparam_fields = HvmModifyVirtualMachineForm.hvparam_fields
        hvparams = hvm_vm.info['hvparams']
        form = HvmModifyVirtualMachineForm(hvm_vm)

        for field in hvparam_fields:
            self.assertEqual(form.fields[field].initial, hvparams[field])

class TestPvmModifyVirtualMachineForm(TestCase, VirtualMachineTestCaseMixin):
    def setUp(self):
        from ganeti_web.tests.rapi_proxy import XEN_PVM_INSTANCE
        global pvm_cluster, pvm_vm

        models.client.GanetiRapiClient = XenRapiProxy
        pvm_cluster = Cluster.objects.create(hostname='test1.pvm_cluster',
            slug='test1')
        pvm_cluster.info = XEN_INFO
        pvm_vm = VirtualMachine.objects.create(hostname='pvm.osuosl',
            cluster=pvm_cluster)
        pvm_vm.info = XEN_PVM_INSTANCE

    def tearDown(self):
        User.objects.all().delete()
        Group.objects.all().delete()
        VirtualMachine.objects.all().delete()
        Cluster.objects.all().delete()

    def test_meta_default_hypervisor(self):
        self.assertEqual(pvm_cluster.info['default_hypervisor'], 'xen-pvm')

    def test_meta_xenrapiproxy_set(self):
        self.assertEqual(models.client.GanetiRapiClient, XenRapiProxy)

    def test_form_defaults(self):
        form = PvmModifyVirtualMachineForm(pvm_vm)

    def test_initial_form_fields(self):
        """
        Test that the form does not contain any extra fields.
        """
        modify_fields = ('vcpus', 'memory', 'nic_link', 'nic_mac', 'os_name')
        hv_fields = PvmModifyVirtualMachineForm.hvparam_fields
        form = PvmModifyVirtualMachineForm(pvm_vm)

        for field in chain(modify_fields, hv_fields):
            self.assertTrue(field in form.fields)

        for field in form.Meta.exclude:
            self.assertFalse(field in form.fields)

    def test_bound_form(self):
        data = dict(
            os_name = 'image+default',
            vcpus = 2,
            memory = 200,
        )
        form = PvmModifyVirtualMachineForm(pvm_vm, data)
        self.assertTrue(form.is_bound)
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_field_initial_values(self):
        """
        Test that fields contain the correct initial values taken from a vm.
        """
        hvparam_fields = PvmModifyVirtualMachineForm.hvparam_fields
        hvparams = pvm_vm.info['hvparams']
        form = PvmModifyVirtualMachineForm(pvm_vm)

        for field in hvparam_fields:
            self.assertEqual(form.fields[field].initial, hvparams[field])
