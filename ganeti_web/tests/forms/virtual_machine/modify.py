from itertools import chain

from django.contrib.auth.models import User, Group
from django.test import TestCase

from ganeti_web import models
from ganeti_web import constants
from ganeti_web.forms.virtual_machine import \
    HvmModifyVirtualMachineForm, KvmModifyVirtualMachineForm, \
    PvmModifyVirtualMachineForm, ReplaceDisksForm, ModifyVirtualMachineForm
from ganeti_web.tests.rapi_proxy import RapiProxy, XenRapiProxy, XEN_INFO, XEN_HVM_INSTANCE, XEN_PVM_INSTANCE
from ganeti_web.tests.views.virtual_machine.base import VirtualMachineTestCaseMixin

__all__ = [
    'TestKvmModifyVirtualMachineForm',
    'TestHvmModifyVirtualMachineForm',
    'TestPvmModifyVirtualMachineForm',
    ]

VirtualMachine = models.VirtualMachine
Cluster = models.Cluster


global cluster, vm


class TestModifyVirtualMachineForm(TestCase, VirtualMachineTestCaseMixin):

    Form = ModifyVirtualMachineForm

    def setUp(self):
        global cluster, vm
        vm, cluster = self.create_virtual_machine()
        vm.refresh()

        self.data = dict(vcpus=2,
            acpi=True,
            disk_cache='default',
            initrd_path='',
            kernel_args='ro',
            kvm_flag='',
            mem_path='',
            migration_downtime=30,
            security_domain='',
            security_model='none',
            usb_mouse='',
            use_chroot=False,
            use_localtime=False,
            vnc_bind_addres='0.0.0.0',
            vnc_tls=False,
            vnc_x509_path='',
            vnc_x509_verify=False,
            memory=512,
            os='image+debian-osgeo',
            disk_type='paravirtual',
            boot_order='disk',
            nic_type='paravirtual',
            nic_count=1,
            nic_link_0='br0',
            nic_mac_0='aa:bb:00:00:33:d2',
            root_path='/dev/vda1',
            kernel_path='/boot/vmlinuz-2.32.6-27-generic',
            serial_console=True,
            cdrom_image_path='')

    def tearDown(self):
        VirtualMachine.objects.all().delete()
        Cluster.objects.all().delete()

    def test_multiple_nic(self):
        data = self.data
        data['nic_count'] = 2
        data['nic_mac_1'] = 'aa:bb:cc:dd:ee:ff'
        data['nic_link_1'] = 'br1'
        form = self.Form(vm, data)

        self.assertTrue("nic_mac_0" in form.fields)
        self.assertTrue("nic_mac_1" in form.fields)
        self.assertTrue("nic_link_0" in form.fields)
        self.assertTrue("nic_link_1" in form.fields)
        self.assertTrue(form.is_valid())

    def test_validate_valid(self):
        form = self.Form(vm)
        print 'wtf [%s]' % form.is_valid()
        print form.data
        self.assertTrue(form.is_valid(), form.errors)

    def test_validate_valid_data(self):
        form = self.Form(vm, self.data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_validate_new_nic(self):
        data = self.data
        data['nic_count'] = 2
        data['nic_mac_1'] = 'aa:bb:cc:dd:ee:ff'
        data['nic_link_1'] = 'br1'
        form = self.Form(vm, data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_validate_remove_nic(self):
        data = self.data
        data['nic_count'] = 2
        data['nic_mac_1'] = None
        data['nic_link_1'] = None
        form = self.Form(vm, data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_validate_missing_nic_mac(self):
        data = self.data
        del data['nic_mac_0']
        form = self.Form(vm, data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_validate_missing_nic_link(self):
        data = self.data
        del data['nic_link_0']
        form = self.Form(vm, data)
        self.assertFalse(form.is_valid())

    def test_initial_base_initial_values(self):
        form = self.Form(vm)
        self.assertEqual(1, form.fields['nic_count'].initial)
        self.assertEqual('br42', form.fields['nic_link_0'].initial)
        self.assertEqual('aa:00:00:c5:47:2e', form.fields['nic_mac_0'].initial)


class TestKvmModifyVirtualMachineForm(TestModifyVirtualMachineForm):

    Form = KvmModifyVirtualMachineForm

    def setUp(self):
        models.client.GanetiRapiClient = RapiProxy
        super(TestKvmModifyVirtualMachineForm, self).setUp()

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

        form = KvmModifyVirtualMachineForm(vm)
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
        vm.refresh()
        form = KvmModifyVirtualMachineForm(vm)
        for field in chain(modify_fields, hv_fields):
            self.assertTrue(field in form.fields, field)

        for field in form.Meta.exclude:
            self.assertFalse(field in form.fields, field)


class TestHvmModifyVirtualMachineForm(TestModifyVirtualMachineForm):

    Form = HvmModifyVirtualMachineForm

    def setUp(self):
        global vm, cluster
        models.client.GanetiRapiClient = XenRapiProxy
        super(TestHvmModifyVirtualMachineForm, self).setUp()
        cluster.info = XEN_INFO.copy()
        cluster.info['default_hypervisor'] = 'xen-hvm'
        vm.info = XEN_HVM_INSTANCE

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

        form = HvmModifyVirtualMachineForm(vm)
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
        form = HvmModifyVirtualMachineForm(vm)

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
        form = HvmModifyVirtualMachineForm(vm)

        for field in hvparam_fields:
            self.assertEqual(form.fields[field].initial, hvparams[field])


class TestPvmModifyVirtualMachineForm(TestModifyVirtualMachineForm):

    Form = PvmModifyVirtualMachineForm
    
    def setUp(self):
        global cluster, vm
        models.client.GanetiRapiClient = XenRapiProxy
        super(TestPvmModifyVirtualMachineForm, self).setUp()
        cluster.info = XEN_INFO
        vm.info = XEN_PVM_INSTANCE

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
        modify_fields = ('vcpus', 'memory', 'nic_count', 'nic_link_0', 'nic_mac_0', 'os')
        hv_fields = PvmModifyVirtualMachineForm.hvparam_fields
        form = PvmModifyVirtualMachineForm(vm)

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
        form = PvmModifyVirtualMachineForm(vm, data)
        self.assertTrue(form.is_bound)
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_field_initial_values(self):
        """
        Test that fields contain the correct initial values taken from a vm.
        """
        hvparam_fields = PvmModifyVirtualMachineForm.hvparam_fields
        hvparams = pvm_vm.info['hvparams']
        form = PvmModifyVirtualMachineForm(vm)

        for field in hvparam_fields:
            self.assertEqual(form.fields[field].initial, hvparams[field])