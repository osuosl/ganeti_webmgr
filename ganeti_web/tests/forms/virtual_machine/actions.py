from django.contrib.auth.models import User
from django.test import TestCase

from ganeti_web import models
from ganeti_web.forms.virtual_machine import ReplaceDisksForm
from ganeti_web.util.proxy import RapiProxy
from ganeti_web.util.proxy.constants import INFO
from ganeti_web.tests.views.virtual_machine.base import VirtualMachineTestCaseMixin
from ganeti_web.util.client import REPLACE_DISK_CHG, REPLACE_DISK_AUTO

__all__ = ['TestReplaceDisksForm']


VirtualMachine = models.VirtualMachine
Cluster = models.Cluster


class TestReplaceDisksForm(TestCase, VirtualMachineTestCaseMixin):

    def setUp(self):
        models.client.GanetiRapiClient = RapiProxy
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
        self.assertEqual([(0,'disk/0')], list(form.fields['disks'].choices) )

        # node choices
        self.assertEqual(set([(u'', u'---------'), (u'gtest1.osuosl.bak', u'gtest1.osuosl.bak'), (u'gtest2.osuosl.bak', u'gtest2.osuosl.bak'), (u'gtest3.osuosl.bak', u'gtest3.osuosl.bak')]), set(form.fields['node'].choices))

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
            node='gtest1.osuosl.bak',
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
