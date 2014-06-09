import copy
from django.utils import unittest
from itertools import chain

from django.test import TestCase

from ganeti_webmgr.ganeti_web import constants

from ...forms import (HvmModifyVirtualMachineForm, KvmModifyVirtualMachineForm,
                      PvmModifyVirtualMachineForm, ModifyVirtualMachineForm)
from ..views.base import VirtualMachineTestCaseMixin

import ganeti_webmgr.utils.proxy.constants
import ganeti_webmgr.utils as utils
from ganeti_webmgr.utils import clear_rapi_cache, client
from ganeti_webmgr.utils.proxy import XenRapiProxy, XenHvmRapiProxy
from ganeti_webmgr.utils.proxy.constants import (
    INFO, INSTANCE, NODE, NODES, XEN_INFO,
    XEN_HVM_INSTANCE, XEN_PVM_INSTANCE,
    OPERATING_SYSTEMS, XEN_OPERATING_SYSTEMS
)

from ganeti_webmgr.clusters.models import Cluster

__all__ = [
    'TestKvmModifyVirtualMachineForm',
    'TestHvmModifyVirtualMachineForm',
    'TestPvmModifyVirtualMachineForm',
]


# This is copy of the utils.get_rapi_client function.  We replace original in
# every test below, so we should somehow bring the original back.
OLD_RAPI_CLIENT = copy.copy(utils.get_rapi_client)


class ModifyVirtualMachineFormTestCase(TestCase, VirtualMachineTestCaseMixin):
    """
    This is abstract test case used by next 3 test cases.  It proxies some of
    the RAPI requests.
    """

    Form = ModifyVirtualMachineForm

    data = dict(vcpus=2,
                acpi=True,
                disk_cache='default',
                initrd_path='',
                kernel_args='ro',
                kvm_flag=None,
                mem_path=None,
                migration_downtime=30,
                security_domain='',
                security_model='none',
                usb_mouse=None,
                use_chroot=False,
                use_localtime=False,
                vnc_bind_address='0.0.0.0',
                vnc_tls=False,
                vnc_x509_path=None,
                vnc_x509_verify=False,
                memory=512,
                os='image+debian-osgeo',
                disk_type='paravirtual',
                boot_order='disk',
                nic_type='paravirtual',
                nic_count=1,
                nic_count_original=1,
                nic_link_0='br0',
                nic_mac_0='aa:bb:00:00:33:d2',
                root_path='/dev/vda1',
                kernel_path='/boot/vmlinuz-2.32.6-27-generic',
                serial_console=True,
                cdrom_image_path='')

    def setUp(self):
        """
        Reset models.client.GanetiRapiClient back to the GanetiRapiClient
          class, so that patching can begin.
        """
        self._data = self.data.copy()

    def tearDown(self):
        self.data = self._data.copy()
        self.vm.delete()
        self.cluster.delete()
        clear_rapi_cache()
        utils.get_rapi_client = OLD_RAPI_CLIENT

    def test_multiple_nic(self):
        data = self.data.copy()
        data['nic_count'] = 2
        data['nic_mac_1'] = 'aa:bb:cc:dd:ee:ff'
        data['nic_link_1'] = 'br1'
        form = self.Form(self.vm, data)

        self.assertTrue("nic_mac_0" in form.fields)
        self.assertTrue("nic_mac_1" in form.fields)
        self.assertTrue("nic_link_0" in form.fields)
        self.assertTrue("nic_link_1" in form.fields)
        self.assertTrue(form.is_valid(), form.errors)

    def test_validate_data(self):
        data = self.data.copy()
        form = self.Form(self.vm, data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_validate_new_nic(self):
        data = self.data.copy()
        data['nic_count'] = 2
        data['nic_mac_1'] = 'aa:bb:cc:dd:ee:ff'
        data['nic_link_1'] = 'br1'
        form = self.Form(self.vm, data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_validate_remove_nic(self):
        data = self.data.copy()
        data['nic_count'] = 1
        data['nic_original'] = 2
        data['nic_mac_1'] = None
        data['nic_link_1'] = None
        form = self.Form(self.vm, data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_validate_missing_nic_mac(self):
        data = self.data.copy()
        del data['nic_mac_0']
        form = self.Form(self.vm, data)
        self.assertFalse(form.is_valid(), form.errors)

    def test_validate_missing_nic_link(self):
        data = self.data.copy()
        del data['nic_link_0']
        form = self.Form(self.vm, data)
        self.assertFalse(form.is_valid())

    def test_initial_base_initial_values(self):
        form = self.Form(self.vm)
        self.assertEqual(1, form.fields['nic_count'].initial)
        self.assertEqual('br42', form.fields['nic_link_0'].initial)
        self.assertEqual('aa:00:00:c5:47:2e', form.fields['nic_mac_0'].initial)


class TestKvmModifyVirtualMachineForm(ModifyVirtualMachineFormTestCase):

    Form = KvmModifyVirtualMachineForm

    def setUp(self):
        super(TestKvmModifyVirtualMachineForm, self).setUp()

        self.vm, self.cluster = self.create_virtual_machine(
            cluster=Cluster(
                hostname='kvm.cluster',
                slug='kvm',
                username='kvmuser',
                password='kvmpass',
            ),
            hostname='kvm.virtualmachine'
        )

        self.cluster.info = INFO.copy()
        self.cluster.refresh()
        self.vm.info = INSTANCE.copy()
        self.vm.refresh()

        self.data['os'] = 'image+ubuntu-lucid'
        self.data['boot_order'] = 'disk'

    def test_meta_rapiproxy_set(self):
        self.assertEqual(self.cluster.info, INFO)
        self.assertEqual(self.vm.info, INSTANCE)

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

        form = KvmModifyVirtualMachineForm(self.vm)
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
        form = KvmModifyVirtualMachineForm(self.vm)
        for field in chain(modify_fields, hv_fields):
            self.assertTrue(field in form.fields, field)

        for field in form.Meta.exclude:
            self.assertFalse(field in form.fields, field)


class TestHvmModifyVirtualMachineForm(ModifyVirtualMachineFormTestCase):

    Form = HvmModifyVirtualMachineForm

    def setUp(self):
        utils.get_rapi_client = lambda: XenRapiProxy

        # self.patches = (
        #     (self.rapi, 'GetNodes', lambda x: NODES),
        #     (self.rapi, 'GetNode', lambda y, x: NODE),
        #     (self.rapi, 'GetInfo', lambda x: XEN_INFO),
        #     (self.rapi, 'GetOperatingSystems',
        #      lambda x: XEN_OPERATING_SYSTEMS),
        #     (self.rapi, 'GetInstance', lambda x, y: XEN_HVM_INSTANCE),
        # )

        super(TestHvmModifyVirtualMachineForm, self).setUp()

        self.vm, self.cluster = self.create_virtual_machine(
            cluster=Cluster(
                hostname='xen-hvm.cluster',
                slug='xen-hvm',
                username='xenuser',
                password='xenpass',
            ),
            hostname='xen-hvm.virtualmachine'
        )

        self.cluster.info = XEN_INFO.copy()
        self.cluster.info['default_hypervisor'] = 'xen-hvm'
        self.vm.info = XEN_HVM_INSTANCE.copy()
        self.vm.refresh()

        # data custom to HVM
        self.data['os'] = 'debootstrap+default'
        self.data['boot_order'] = 'cd'

    def test_meta_xenrapiproxy_set(self):
        self.assertEqual(set(self.vm.info), set(XEN_HVM_INSTANCE))
        self.assertEqual(set(self.cluster.info), set(XEN_INFO))

    def test_meta_default_hypervisor(self):
        self.assertEqual(self.cluster.info['default_hypervisor'], 'xen-hvm')

    def test_form_defaults(self):
        choices = constants.HVM_CHOICES
        disk_type = choices['disk_type']
        nic_type = choices['nic_type']
        boot_order = choices['boot_order']

        form = self.Form(self.vm)
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
        hv_fields = self.Form.hvparam_fields
        form = self.Form(self.vm)

        for field in chain(modify_fields, hv_fields):
            self.assertTrue(field in form.fields, field)

        for field in form.Meta.exclude:
            self.assertFalse(field in form.fields, field)

    @unittest.skip("Skipping broken")
    def test_field_initial_values(self):
        """
        Test that fields contain the correct initial values taken from a vm.
        """
        hvparam_fields = self.Form.hvparam_fields
        hvparams = self.vm.info['hvparams']
        form = self.Form(self.vm)

        # print hvparam_fields
        # print hvparams
        for field in hvparam_fields:
            self.assertEqual(form.fields[field].initial, hvparams[field])


class TestPvmModifyVirtualMachineForm(ModifyVirtualMachineFormTestCase):

    Form = PvmModifyVirtualMachineForm

    def setUp(self):
        utils.get_rapi_client = lambda: XenRapiProxy

        super(TestPvmModifyVirtualMachineForm, self).setUp()

        self.vm, self.cluster = self.create_virtual_machine(
            cluster=Cluster(
                hostname='xen-pvm.cluster',
                slug='xen-pvm',
                username='pvmuser',
                password='pvmpass',
            ),
            hostname='pvm.virtualmachine'
        )

        self.cluster.info = XEN_INFO.copy()
        self.vm.info = XEN_PVM_INSTANCE.copy()
        self.vm.refresh()

        self.data['os'] = 'debootstrap+default'

    def test_meta_default_hypervisor(self):
        """
        Make sure that the default hypervisor is correct for this test.
        """
        self.assertEqual(self.cluster.info['default_hypervisor'], 'xen-pvm')

    def test_meta_xenpvm_info_set(self):
        """
        Test that cluster info and vm info are set to their correct values.
        """
        self.assertEqual(set(self.cluster.info), set(XEN_INFO))
        self.assertEqual(set(self.vm.info), set(XEN_PVM_INSTANCE))

    def test_form_defaults(self):
        """
        TODO: Make this look like the HVM form test_form_defaults, but for Pvm
        """
        PvmModifyVirtualMachineForm(self.vm)

    def test_initial_form_fields(self):
        """
        Test that the form does not contain any extra fields.
        """
        modify_fields = ('vcpus', 'memory', 'nic_count',
                         'nic_link_0', 'nic_mac_0', 'os')
        hv_fields = PvmModifyVirtualMachineForm.hvparam_fields
        form = PvmModifyVirtualMachineForm(self.vm)

        for field in chain(modify_fields, hv_fields):
            self.assertTrue(field in form.fields, field)

        for field in form.Meta.exclude:
            self.assertFalse(field in form.fields, field)

    def test_bound_form(self):
        """
        Basic test to make sure the form is bound when data is passed.
          This goes back to when data was not being bound after being passed
          to the form as data, and the initial kwarg was binding the data.
        """
        data = dict(
            os='image+default',
            vcpus=2,
            memory=200,
            nic_count=1,
            nic_count_original=1,
            nic_link_0='br0',
            nic_mac_0='aa:bb:cc:dd:ee:ff'
        )
        form = PvmModifyVirtualMachineForm(self.vm, data)
        self.assertTrue(form.is_bound)
        self.assertTrue(form.is_valid(), msg=form.errors)

    def test_field_initial_values(self):
        """
        Test that fields contain the correct initial values taken from a vm.
        """
        hvparam_fields = PvmModifyVirtualMachineForm.hvparam_fields
        hvparams = self.vm.info['hvparams']
        form = PvmModifyVirtualMachineForm(self.vm)

        for field in hvparam_fields:
            self.assertEqual(form.fields[field].initial, hvparams[field])
