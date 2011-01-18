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

__all__ = ('TestGanetiErrorModel',)

class TestGanetiErrorModel(TestCase):
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

    # TODO: add tests for clusters/vms in get_errors
    # TODO: maybe split into individual tests? Not sure
    def test_manager_methods(self):
        """
        Test useful GanetiErrorManager methods:
        * store_error
        * get_errors
        * clear_errors
        * clear_error
        * remove_errors

        Verifies:
            * all those methods are free of errors
        """
        cluster0 = self.create_model(Cluster, hostname="test0", slug="OSL_TEST0")
        cluster1 = self.create_model(Cluster, hostname="test1", slug="OSL_TEST1")
        cluster2 = self.create_model(Cluster, hostname="test2", slug="OSL_TEST2")
        cluster0.save()
        cluster1.save()
        cluster2.save()
        vm0 = self.create_model(VirtualMachine,cluster=cluster0, hostname="vm0.test.org")
        vm1 = self.create_model(VirtualMachine,cluster=cluster1, hostname="vm1.test.org")
        vm0.save()
        vm1.save()

        msg = client.GanetiApiError("Simulating an error", 777)
        RapiProxy.error = msg

        # test store_error
        store_error = GanetiError.objects.store_error
        store_error(str(msg), msg.code, obj=cluster0)
        store_error(str(msg), msg.code, obj=cluster1)
        store_error(str(msg), msg.code, obj=cluster2)
        store_error(str(msg), msg.code, obj=vm0)
        store_error(str(msg), msg.code, obj=vm1)

        # test get_errors
        get_errors = GanetiError.objects.get_errors
        
        errors = get_errors(msg=str(msg))
        self.assertEqual(len(errors), 5)
        errors = get_errors(msg=str(msg) + "NOTHING")
        self.assertEqual(len(errors), 0)

        errors = get_errors(code=msg.code)
        self.assertEqual(len(errors), 5)
        errors = get_errors(code=msg.code + 123)
        self.assertEqual(len(errors), 0)

        errors = get_errors(obj=cluster0)
        self.assertEqual(len(errors), 2)
        errors = get_errors(obj=cluster1)
        self.assertEqual(len(errors), 2)
        errors = get_errors(obj=cluster2)
        self.assertEqual(len(errors), 1)

        errors = get_errors(obj=vm0)
        self.assertEqual(len(errors), 1)
        errors = get_errors(obj=vm1)
        self.assertEqual(len(errors), 1)

        errors = get_errors(cls=Cluster, obj=Cluster.objects.all())
        self.assertEqual(len(errors), 5)
        errors = get_errors(cls=VirtualMachine, obj=VirtualMachine.objects.all())
        self.assertEqual(len(errors), 2)

        # test clear_error(s)
        clear_error = GanetiError.objects.clear_error
        clear_errors = GanetiError.objects.clear_errors

        errors = get_errors()
        self.assertEqual(len(errors), 5)
        errors = get_errors(cleared=False).order_by("id")
        self.assertEqual(len(errors), 5)

        clear_error(errors[0].id)
        errors = get_errors()
        self.assertEqual(len(errors), 5)
        errors = get_errors(cleared=False)
        self.assertEqual(len(errors), 4)

        clear_errors(obj=cluster2)
        errors = get_errors()
        self.assertEqual(len(errors), 5)
        errors = get_errors(cleared=False)
        self.assertEqual(len(errors), 3)

        clear_errors(obj=vm1)
        errors = get_errors()
        self.assertEqual(len(errors), 5)
        errors = get_errors(cleared=False)
        self.assertEqual(len(errors), 2)

        clear_errors(msg=str(msg))
        errors = get_errors()
        self.assertEqual(len(errors), 5)
        errors = get_errors(cleared=False)
        self.assertEqual(len(errors), 0)

        # test remove_errors
        remove_errors = GanetiError.objects.remove_errors

        errors = get_errors()
        self.assertEqual(len(errors), 5)

        remove_errors(obj=cluster2)
        errors = get_errors()
        self.assertEqual(len(errors), 4)

        remove_errors(obj=vm1)
        errors = get_errors()
        self.assertEqual(len(errors), 3)

        remove_errors(msg=str(msg))
        errors = get_errors()
        self.assertEqual(len(errors), 0)


    def refresh(self, object):
        """
        NOTE: this test is borrowed from TestCachedClusterObject.

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
            * error will be saved as GanetiError object
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

        msg = client.GanetiApiError("Simulating an error", 777)
        RapiProxy.error = msg

        # force an error on all objects to test its capture
        for i in (cluster0, cluster1, vm0, vm1):
            i.refresh()
            self.assertEqual(str(msg), i.error)

            # get errors for object
            # TODO: check log format
            if isinstance(i, VirtualMachine):
                errors = GanetiError.objects.get_errors(obj=i.cluster)
                self.assertEqual(2, len(errors))
                self.assertEqual(errors[0].cleared, False)
                self.assertEqual(errors[1].cleared, False)
                self.assertEqual(errors[0].msg, str(msg))
                self.assertEqual(errors[1].msg, str(msg))
                self.assertEqual(errors[0].code, msg.code)
                self.assertEqual(errors[1].code, msg.code)

                cleared = GanetiError.objects.get_errors(obj=i.cluster, cleared=True)
                self.assertEqual(0, len(cleared))

            else:
                errors = GanetiError.objects.get_errors(obj=i)
                self.assertEqual(1, len(errors))
                self.assertEqual(errors[0].cleared, False)
                self.assertEqual(errors[0].msg, str(msg))
                self.assertEqual(errors[0].code, msg.code)

                cleared = GanetiError.objects.get_errors(obj=i, cleared=True)
                self.assertEqual(0, len(cleared))
        
        # set all errors as cleared  and test if it was a success
        for i in (cluster0, cluster1, vm0, vm1):
            if isinstance(i, VirtualMachine):
                GanetiError.objects.clear_errors(obj=i.cluster)

                cleared = GanetiError.objects.get_errors(obj=i.cluster, cleared=True)
                self.assertEqual(2, len(cleared))
                self.assertEqual(cleared[0].cleared, True)
                self.assertEqual(cleared[1].cleared, True)
                self.assertEqual(cleared[0].msg, str(msg))
                self.assertEqual(cleared[1].msg, str(msg))
                self.assertEqual(cleared[0].code, msg.code)
                self.assertEqual(cleared[1].code, msg.code)

            else:
                GanetiError.objects.clear_errors(obj=i)

                cleared = GanetiError.objects.get_errors(obj=i, cleared=True)
                self.assertEqual(2, len(cleared))
                self.assertEqual(cleared[0].cleared, True)
                self.assertEqual(cleared[1].cleared, True)
                self.assertEqual(cleared[0].msg, str(msg))
                self.assertEqual(cleared[1].msg, str(msg))
                self.assertEqual(cleared[0].code, msg.code)
                self.assertEqual(cleared[1].code, msg.code)

        # clear the error and retry
        RapiProxy.error = None

        for i in (cluster0, cluster1, vm0, vm1):
            self.refresh(i)
            self.assertEqual(None, i.error)
