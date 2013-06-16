from django.contrib.auth.models import User
from django.test import TestCase

from utils.proxy import RapiProxy
from utils.proxy.constants import INFO
from utils import client
from client import REPLACE_DISK_CHG, REPLACE_DISK_AUTO

from ...forms import ReplaceDisksForm
from ..views.base import VirtualMachineTestCaseMixin

from virtualmachines.models import VirtualMachine
from clusters.models import Cluster

__all__ = ['TestReplaceDisksForm']


class TestReplaceDisksForm(TestCase, VirtualMachineTestCaseMixin):

    def setUp(self):
        client.GanetiRapiClient = RapiProxy
        self.vm, self.cluster = self.create_virtual_machine()
        self.cluster.info = INFO
        self.vm.refresh()

    def tearDown(self):
        User.objects.all().delete()
        VirtualMachine.objects.all().delete()
        Cluster.objects.all().delete()

    def test_bound_form(self):
        """
        tests intial values and choices are intitialized correctly
        """
        form = ReplaceDisksForm(self.vm)

        # disk choices
        self.assertEqual([(0, 'disk/0')], list(form.fields['disks'].choices))

        # node choices
        self.assertEqual(set([(u'', u'---------'),
                         (u'gtest1.example.bak', u'gtest1.example.bak'),
                         (u'gtest2.example.bak', u'gtest2.example.bak'),
                         (u'gtest3.example.bak', u'gtest3.example.bak')]),
                         set(form.fields['node'].choices))

    def test_auto(self):
        data = dict(
            mode=REPLACE_DISK_AUTO,
            disks='',
            node='',
            iallocator=''
        )
        form = ReplaceDisksForm(self.vm, data)
        form.is_valid()
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

    def test_replace_new_secondary_without_node(self):
        data = dict(
            mode=REPLACE_DISK_CHG,
            disks='',
            node=None,
            iallocator=False
        )
        form = ReplaceDisksForm(self.vm, data)
        self.assertFalse(form.is_valid(), form.errors)

    def test_replace_new_secondary_with_node(self):
        data = dict(
            mode=REPLACE_DISK_CHG,
            disks='',
            node='gtest1.example.bak',
            iallocator=''
        )
        form = ReplaceDisksForm(self.vm, data)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()

    def test_replace_new_secondary_with_iallocator(self):
        data = dict(
            mode=REPLACE_DISK_CHG,
            disks='',
            node='',
            iallocator=True,
            iallocator_hostname='foo.bar.com'
        )
        form = ReplaceDisksForm(self.vm, data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_clean_disks_single(self):
        data = dict(
            mode=REPLACE_DISK_AUTO,
            disks=[0],
            node='',
            iallocator=''
        )
        form = ReplaceDisksForm(self.vm, data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual('0', form.cleaned_data['disks'])
        form.save()

    def test_clean_disks_multiple(self):
        data = dict(
            mode=REPLACE_DISK_AUTO,
            disks=[0, 0],
            node='',
            iallocator=''
        )
        form = ReplaceDisksForm(self.vm, data)
        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual('0,0', form.cleaned_data['disks'])
        form.save()
