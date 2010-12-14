# Copyright (C) 2010 Oregon State University et al.
# Copyright (C) 2010 Greek Research and Technology Network
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.

from datetime import datetime, time
import time

from django.test import TestCase

from ganeti import models
from ganeti.cache import update_cache
from ganeti.tests.rapi_proxy import RapiProxy, INSTANCES_BULK
from ganeti.tests.utils import MuteStdout
from ganeti.tests.virtual_machine import VirtualMachineTestCaseMixin


VirtualMachine = models.VirtualMachine
Cluster = models.Cluster


class TestCacheUpdater(TestCase, VirtualMachineTestCaseMixin):

    def setUp(self):
        self.tearDown()
        models.client.GanetiRapiClient = RapiProxy

    def tearDown(self):
        VirtualMachine.objects.all().delete()
        Cluster.objects.all().delete()
    
    def test_no_updates(self):
        """
        Test running the updater running when no vms need to be updated
        """
        vm0, cluster = self.create_virtual_machine()
        vm1, chaff = self.create_virtual_machine(cluster, 'vm2.osuosl.bak')
        
        os = 'image+gentoo-hardened-cf'
        mtime_timestamp = 1285883000.8692000
        mtime = datetime.fromtimestamp(mtime_timestamp)
        cached = datetime.now()
        
        # set data so that mtime is up to date.  include a data change that
        # can be test for
        data = list(INSTANCES_BULK)
        data[0]['mtime'] = mtime_timestamp
        data[1]['mtime'] = mtime_timestamp
        cluster.rapi.GetInstances.response = data
        VirtualMachine.objects.all().update(mtime=mtime, cached=cached, \
                                operating_system='image+fake', status='running')
        
        # run updater and refresh the objects from the db
        with MuteStdout():
            update_cache()
        vm0 = VirtualMachine.objects.filter(pk=vm0.id).values('mtime','cached','status','operating_system')[0]
        vm1 = VirtualMachine.objects.filter(pk=vm1.id).values('mtime','cached','status','operating_system')[0]
        
        # properties should not be updated because mtime and status indicated it
        # was already up to date
        self.assertNotEqual(os, vm0['operating_system'])
        self.assertNotEqual(os, vm1['operating_system'])
        
        if cached > datetime.fromtimestamp(float(vm0['cached'])):
            self.fail('cache is not newer: %s, %s' % (cached, vm0.cached))
        
        if cached > datetime.fromtimestamp(float(vm1['cached'])):
            self.fail('cache is not newer: %s, %s' % (cached, vm1.cached))

    def test_updated_mtime(self):
        """
        tests that newer mtime results in update
        """
        vm0, cluster = self.create_virtual_machine()
        vm1, chaff = self.create_virtual_machine(cluster, 'vm2.osuosl.bak')
        
        os = 'image+gentoo-hardened-cf'
        mtime_timestamp = 1285883000.1234000
        mtime = datetime.fromtimestamp(mtime_timestamp)
        new_mtime_timestamp = 1999999999.8692000
        new_mtime = datetime.fromtimestamp(new_mtime_timestamp)
        cached = datetime.now()
        
        # set data so that mtime is up to date.  include a data change that
        # can be test for
        data = list(INSTANCES_BULK)
        data[0]['mtime'] = new_mtime_timestamp
        data[1]['mtime'] = new_mtime_timestamp
        cluster.rapi.GetInstances.response = data
        
        VirtualMachine.objects.all().update(mtime=mtime, cached=cached, \
                            operating_system='image+fake', status='running')
        
        # run updater and refresh the objects from the db
        with MuteStdout():
            update_cache()
        vm0 = VirtualMachine.objects.filter(pk=vm0.id).values('mtime','cached','status','operating_system')[0]
        vm1 = VirtualMachine.objects.filter(pk=vm1.id).values('mtime','cached','status','operating_system')[0]
        
        # check for properties that are updated
        self.assertEqual(os, vm0['operating_system'])
        self.assertEqual(os, vm1['operating_system'])
        self.assertEqual(new_mtime_timestamp, float(vm0['mtime']))
        self.assertEqual(new_mtime_timestamp, float(vm1['mtime']))
        self.assertEqual("running", vm0['status'])
        self.assertEqual("running", vm1['status'])
        
        
        if cached > datetime.fromtimestamp(float(vm0['cached'])):
            self.fail('cache is not newer: %s, %s' % (cached, vm0.cached))
        
        if cached > datetime.fromtimestamp(float(vm1['cached'])):
            self.fail('cache is not newer: %s, %s' % (cached, vm1.cached))
    
    def test_null_timestamps(self):
        """
        Tests that the cache updater can handle updating records with null
        timestamps
        """
        vm0, cluster = self.create_virtual_machine()
        vm1, chaff = self.create_virtual_machine(cluster, 'vm2.osuosl.bak')
        
        os = 'image+gentoo-hardened-cf'
        mtime_timestamp = 1285883000.8692000
        mtime = datetime.fromtimestamp(mtime_timestamp)
        cached = datetime.now()
        
        # set data so that mtime is up to date.  include a data change that
        # can be test for
        data = list(INSTANCES_BULK)
        data[0]['mtime'] = mtime_timestamp
        data[1]['mtime'] = mtime_timestamp
        cluster.rapi.GetInstances.response = data
        VirtualMachine.objects.all().update(mtime=None, cached=None, \
                                operating_system='image+fake', status='running')
        
        # run updater and refresh the objects from the db
        with MuteStdout():
            update_cache()
        vm0 = VirtualMachine.objects.filter(pk=vm0.id).values('mtime','cached','status','operating_system')[0]
        vm1 = VirtualMachine.objects.filter(pk=vm1.id).values('mtime','cached','status','operating_system')[0]
        
        # properties should not be updated because mtime and status indicated it
        # was already up to date
        self.assertEqual(os, vm0['operating_system'])
        self.assertEqual(os, vm1['operating_system'])
        self.assertEqual(mtime_timestamp, float(vm0['mtime']))
        self.assertEqual(mtime_timestamp, float(vm1['mtime']))
        self.assertEqual("running", vm0['status'])
        self.assertEqual("running", vm1['status'])
        
        if cached > datetime.fromtimestamp(float(vm0['cached'])):
            self.fail('cache is not newer: %s, %s' % (cached, vm0.cached))
        
        if cached > datetime.fromtimestamp(float(vm1['cached'])):
            self.fail('cache is not newer: %s, %s' % (cached, vm1.cached))
    
    def test_missing_vms(self):
        """
        Tests the cache updater importing missing vms
        """
        vm0, cluster = self.create_virtual_machine()
        
        os = 'image+gentoo-hardened-cf'
        mtime_timestamp = 1285883000.8692000
        mtime = datetime.fromtimestamp(mtime_timestamp)
        cached = datetime.now()
        
        # set data so that mtime is up to date.  include a data change that
        # can be test for
        data = list(INSTANCES_BULK)
        data[0]['mtime'] = mtime_timestamp
        data[1]['mtime'] = mtime_timestamp
        cluster.rapi.GetInstances.response = data
        VirtualMachine.objects.all().update(mtime=None, cached=None, \
                                operating_system='image+fake', status='running')
        
        # run updater and refresh the objects from the db
        with MuteStdout():
            update_cache()
        self.assert_(VirtualMachine.objects.filter(hostname='vm2.osuosl.bak').exists())
        vm0 = VirtualMachine.objects.filter(pk=vm0.id).values('mtime','cached','status','operating_system')[0]
        vm1 = VirtualMachine.objects.filter(hostname='vm2.osuosl.bak').values('mtime','cached','status','operating_system')[0]
        
        # properties should not be updated because mtime and status indicated it
        # was already up to date
        self.assertEqual(os, vm0['operating_system'])
        self.assertEqual(os, vm1['operating_system'])
        self.assertEqual(mtime_timestamp, float(vm0['mtime']))
        self.assertEqual(mtime_timestamp, float(vm1['mtime']))
        self.assertEqual("running", vm0['status'])
        self.assertEqual("running", vm1['status'])
        
        if cached > datetime.fromtimestamp(float(vm0['cached'])):
            self.fail('cache is not newer: %s, %s' % (cached, vm0.cached))
        
        if cached > datetime.fromtimestamp(float(vm1['cached'])):
            self.fail('cache is not newer: %s, %s' % (cached, vm1.cached))
    
    def test_updated_status(self):
        """
        Test that updater detects and updates status changes
        """
        vm0, cluster = self.create_virtual_machine()
        vm1, chaff = self.create_virtual_machine(cluster, 'vm2.osuosl.bak')
        
        os = 'image+gentoo-hardened-cf'
        mtime_timestamp = 1285883000.8692000
        mtime = datetime.fromtimestamp(mtime_timestamp)
        cached = datetime.now()
        
        # set data so that mtime is up to date.  include a data change that
        # can be test for
        data = list(INSTANCES_BULK)
        data[0]['mtime'] = mtime_timestamp
        data[1]['mtime'] = mtime_timestamp
        cluster.rapi.GetInstances.response = data
        VirtualMachine.objects.all().update(mtime=mtime, cached=cached, \
                            operating_system='image+fake', status='ADMIN_down')
        
        # run updater and refresh the objects from the db
        with MuteStdout():
            update_cache()
        vm0 = VirtualMachine.objects.filter(pk=vm0.id).values('mtime','cached','status','operating_system')[0]
        vm1 = VirtualMachine.objects.filter(pk=vm1.id).values('mtime','cached','status','operating_system')[0]
        
        # check for properties that are updated
        self.assertEqual(os, vm0['operating_system'])
        self.assertEqual(os, vm1['operating_system'])
        self.assertEqual(mtime_timestamp, float(vm0['mtime']))
        self.assertEqual(mtime_timestamp, float(vm1['mtime']))
        self.assertEqual("running", vm0['status'])
        self.assertEqual("running", vm1['status'])
        
        if cached > datetime.fromtimestamp(float(vm0['cached'])):
            self.fail('cache is not newer: %s, %s' % (cached, vm0.cached))
        
        if cached > datetime.fromtimestamp(float(vm1['cached'])):
            self.fail('cache is not newer: %s, %s' % (cached, vm1.cached))