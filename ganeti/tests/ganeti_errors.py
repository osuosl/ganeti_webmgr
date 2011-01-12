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

from datetime import datetime

#from django.conf import settings
from django.test import TestCase

from util import client
from ganeti.tests.call_proxy import CallProxy
from ganeti.tests.rapi_proxy import RapiProxy
from django.contrib.auth.models import User, Group
from ganeti import models

models.client.GanetiRapiClient = RapiProxy

VirtualMachine = models.VirtualMachine
Cluster = models.Cluster
GanetiError = models.GanetiError
GanetiErrorManager = models.GanetiErrorManager

__all__ = ('TestGanetiErrorObject',)

class TestGanetiErrorObject(TestCase):
    """
    Class for testing ganeti error storage.
    """
    
    def setUp(self):
        self.tearDown()
    
    def create_model(self, class_, *args, **kwargs):
        """
        create an instance of the model being tested, this will instrument
        some methods of the model to check if they have been called
        """
        object = class_(*args, **kwargs)
        
        # patch model class
        CallProxy.patch(object, 'parse_transient_info')
        CallProxy.patch(object, 'parse_persistent_info')
        CallProxy.patch(object, '_refresh')
        CallProxy.patch(object, 'load_info')
        CallProxy.patch(object, 'save')
        return object
    
    def tearDown(self):
        VirtualMachine.objects.all().delete()
        Cluster.objects.all().delete()
        GanetiError.objects.all().delete()

    def test_refresh(self, object):
        """
        Test forced refresh of cached data
        
        Verifies:
            * Object specific refresh is called
            * Info is parsed
            * Object is saved
            * Cache time is updated
        """
        now = datetime.now()
        object.refresh()
        
        object._refresh.assertCalled(self)
        object.parse_transient_info.assertCalled(self)
        object.parse_persistent_info.assertCalled(self)
        self.assertEqual(1, len(object.parse_persistent_info.calls))
        self.assert_(object.id)
        self.assertNotEqual(None, object.cached)
        self.assert_(now < object.cached, "Cache time should be newer")
    
    def test_refresh_error(self):
        """
        Test an error during refresh
        
        Verifies:
            * error will be saved in object.error
            * successful refresh after will clear error
        """
        cluster0 = self.create_model(Cluster, hostname="test0", slug="OSL_TEST0")
        cluster1 = self.create_model(Cluster, hostname="test1", slug="OSL_TEST1")
        cluster0.save()
        cluster1.save()
        vm0 = self.create_model(VirtualMachine,cluster=cluster0, hostname="vm0.test.org")
        vm1 = self.create_model(VirtualMachine,cluster=cluster1, hostname="vm1.test.org")
        vm0.save()
        vm1.save()

        msg = client.GanetiApiError("Simulating an error")
        RapiProxy.error = msg

        # force an error on all objects to test its capture
        for i in (cluster0, cluster1, vm0, vm1):
            i.refresh()
            self.assertEqual(str(msg), i.error)

            # get errors for object
            if isinstance(i, VirtualMachine):
                print GanetiError.objects.get_errors(cluster=i.cluster)
            else:
                print GanetiError.objects.get_errors(cluster=i)
            # check for log format
            # set as fixed
            # get again in last loop
        
        # clear the error and retry
        RapiProxy.error = None

        for i in (cluster0, cluster1, vm0, vm1):
            self.test_refresh(i)
            self.assertEqual(None, i.error)
