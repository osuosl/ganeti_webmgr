from itertools import chain

from django.contrib.auth.models import User, Group
from django.test import TestCase

from ganeti_web import models
from ganeti_web import constants
from ganeti_web.forms.virtual_machine import \
    HvmModifyVirtualMachineForm, KvmModifyVirtualMachineForm, \
    PvmModifyVirtualMachineForm, ReplaceDisksForm
from ganeti_web.tests.rapi_proxy import RapiProxy, XenRapiProxy, XEN_INFO
from ganeti_web.tests.views.virtual_machine.base import VirtualMachineTestCaseMixin

__all__ = [
    'TestKvmModifyVirtualMachineForm',
    'TestHvmModifyVirtualMachineForm',
    'TestPvmModifyVirtualMachineForm',
    ]

VirtualMachine = models.VirtualMachine
Cluster = models.Cluster


global kvm_cluster, hvm_cluster, pvm_cluster
global kvm_vm, hvm_vm, pvm_vm


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
        modify_fields = ('vcpus', 'memory', 'nic_link_0', 'nic_mac_0', 'os')
        hv_fields = KvmModifyVirtualMachineForm.hvparam_fields
        kvm_vm.refresh()
        form = KvmModifyVirtualMachineForm(kvm_vm)
        for field in chain(modify_fields, hv_fields):
            self.assertTrue(field in form.fields, field)

        for field in form.Meta.exclude:
            self.assertFalse(field in form.fields, field)


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
        modify_fields = ('vcpus', 'memory', 'nic_link_0', 'nic_mac_0', 'os')
        hv_fields = HvmModifyVirtualMachineForm.hvparam_fields
        form = HvmModifyVirtualMachineForm(hvm_vm)

        for field in chain(modify_fields, hv_fields):
            self.assertTrue(field in form.fields, field)

        for field in form.Meta.exclude:
            self.assertFalse(field in form.fields, field)
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
        modify_fields = ('vcpus', 'memory', 'nic_link_0', 'nic_mac_0', 'os')
        hv_fields = PvmModifyVirtualMachineForm.hvparam_fields
        form = PvmModifyVirtualMachineForm(pvm_vm)

        for field in chain(modify_fields, hv_fields):
            self.assertTrue(field in form.fields, field)

        for field in form.Meta.exclude:
            self.assertFalse(field in form.fields, field)

    def test_bound_form(self):
        data = dict(
            os = 'image+default',
            vcpus = 2,
            memory = 200,
            nic_count=1,
            nic_link_0='br0'
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