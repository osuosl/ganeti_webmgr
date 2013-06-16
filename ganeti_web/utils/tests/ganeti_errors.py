# Copyright (C) 2010 Oregon State University et al.
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

from django.test import TestCase
from django.test.client import Client

from .. import client
from ..proxy import RapiProxy, CallProxy

from django.contrib.auth.models import User

from virtualmachines.models import VirtualMachine
from clusters.models import Cluster
from ..models import GanetiError

__all__ = ('TestGanetiErrorModel', 'TestErrorViews')


class TestGanetiErrorBase():
    """
    Class for testing ganeti error storage.
    """

    def setUp(self):
        self.tearDown()
        client.GanetiRapiClient = RapiProxy

    def tearDown(self):
        VirtualMachine.objects.all().delete()
        Cluster.objects.all().delete()
        GanetiError.objects.all().delete()
        RapiProxy.error = None

    def create_model(self, class_, *args, **kwargs):
        """
        create an instance of the model being tested, this will instrument
        some methods of the model to check if they have been called
        """
        obj = class_.objects.create(*args, **kwargs)

        # patch model class
        CallProxy.patch(obj, 'parse_transient_info')
        CallProxy.patch(obj, 'parse_persistent_info')
        CallProxy.patch(obj, '_refresh')
        CallProxy.patch(obj, 'load_info')
        CallProxy.patch(obj, 'save')
        return obj


class TestGanetiErrorModel(TestGanetiErrorBase, TestCase):
    """
    Class for testing ganeti error storage.
    """

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
        cluster0 = self.create_model(Cluster, hostname="test0",
                                     slug="OSL_TEST0")
        cluster1 = self.create_model(Cluster, hostname="test1",
                                     slug="OSL_TEST1")
        cluster2 = self.create_model(Cluster, hostname="test2",
                                     slug="OSL_TEST2")
        vm0 = self.create_model(VirtualMachine, cluster=cluster0,
                                hostname="vm0.test.org")
        vm1 = self.create_model(VirtualMachine, cluster=cluster1,
                                hostname="vm1.test.org")

        msg = client.GanetiApiError("Simulating an error", 777)
        RapiProxy.error = msg

        # test store_error
        store_error = GanetiError.store_error

        # Duplicated, to ensure store_error only stores one error.
        store_error(str(msg), obj=cluster0, code=msg.code)
        store_error(str(msg), obj=cluster0, code=msg.code)

        store_error(str(msg), obj=cluster1, code=msg.code)
        store_error(str(msg), obj=cluster2, code=msg.code)
        store_error(str(msg), obj=vm0, code=msg.code)
        store_error(str(msg), obj=vm1, code=msg.code)

        # test get_errors
        get_errors = GanetiError.objects.get_errors

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

        errors = get_errors(obj=Cluster.objects.all())
        self.assertEqual(len(errors), 5)
        errors = get_errors(obj=VirtualMachine.objects.all())
        self.assertEqual(len(errors), 2)

        # test clear_error(s)
        clear_errors = GanetiError.objects.clear_errors

        clear_errors(obj=cluster2)
        errors = GanetiError.objects.filter(cleared=False)
        self.assertEqual(len(errors), 4)

        clear_errors(obj=vm1)
        errors = GanetiError.objects.filter(cleared=False)
        self.assertEqual(len(errors), 3)

        GanetiError.objects.filter(msg=str(msg)).clear_errors()
        errors = GanetiError.objects.filter(cleared=False)
        self.assertEqual(len(errors), 0)

        get_errors(obj=cluster2).delete()
        errors = GanetiError.objects.all()
        self.assertEqual(len(errors), 4)

        get_errors(obj=vm1).delete()
        errors = GanetiError.objects.all()
        self.assertEqual(len(errors), 3)

        GanetiError.objects.filter(msg=str(msg)).delete()
        errors = GanetiError.objects.all()
        self.assertEqual(len(errors), 0)

    def test_specified_code_values(self):
        """
        Test if errors with code in (401, 404) are stored in a proper way.
        See tickets #2877, #2883.

        Verifies:
            * Manager store_error works properly for specific code numbers
        """
        cluster0 = self.create_model(Cluster, hostname="test0",
                                     slug="OSL_TEST0")
        vm0 = self.create_model(VirtualMachine, cluster=cluster0,
                                hostname="vm0.test.org")

        msg0 = client.GanetiApiError("Simulating 401 error", 401)
        msg1 = client.GanetiApiError("Simulating 404 error", 404)
        RapiProxy.error = msg0

        store_error = GanetiError.store_error
        get_errors = GanetiError.objects.get_errors

        # 401 - cluster
        store_error(str(msg0), obj=cluster0, code=msg0.code)
        errors = get_errors(obj=cluster0)
        self.assertEqual(len(errors), 1)
        errors = get_errors(obj=vm0)
        self.assertEqual(len(errors), 0)
        get_errors(obj=cluster0).delete()

        # 401 - VM
        store_error(str(msg0), obj=vm0, code=msg0.code)
        errors = get_errors(obj=cluster0)
        self.assertEqual(len(errors), 1)
        errors = get_errors(obj=vm0)
        self.assertEqual(len(errors), 0)
        get_errors(obj=cluster0).delete()
        get_errors(obj=vm0).delete()

        # 404 - VM
        store_error(str(msg1), obj=vm0, code=msg1.code)
        errors = get_errors(obj=cluster0)
        self.assertEqual(len(errors), 1)
        errors = get_errors(obj=vm0)
        self.assertEqual(len(errors), 1)
        get_errors(obj=cluster0).delete()
        get_errors(obj=vm0).delete()

        # 404 - cluster
        store_error(str(msg1), obj=cluster0, code=msg1.code)
        errors = get_errors(obj=cluster0)
        self.assertEqual(len(errors), 1)
        errors = get_errors(obj=vm0)
        self.assertEqual(len(errors), 0)

        # 404 - VM, but error is really with cluster
        store_error(str(msg1), obj=vm0, code=msg1.code)
        errors = get_errors(obj=cluster0)
        self.assertEqual(len(errors), 1)
        errors = get_errors(obj=vm0)
        self.assertEqual(len(errors), 0)
        get_errors(obj=cluster0).delete()

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
        self.assertTrue(object.id)
        self.assertNotEqual(None, object.cached)
        self.assertTrue(now < object.cached, "Cache time should be newer")

    def test_refresh_error(self):
        """
        Test an error during refresh

        Verifies:
            * error will be saved as GanetiError object
            * successful refresh after will clear error
        """
        cluster0 = self.create_model(Cluster, hostname="test0",
                                     slug="OSL_TEST0")
        cluster1 = self.create_model(Cluster, hostname="test1",
                                     slug="OSL_TEST1")
        vm0 = self.create_model(VirtualMachine, cluster=cluster0,
                                hostname="vm0.test.org")
        vm1 = self.create_model(VirtualMachine, cluster=cluster1,
                                hostname="vm1.test.org")

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

                qs = GanetiError.objects.filter(cleared=True)
                cleared = qs.get_errors(obj=i.cluster)
                self.assertEqual(0, len(cleared))

            else:
                errors = GanetiError.objects.get_errors(obj=i)
                self.assertEqual(1, len(errors))
                self.assertEqual(errors[0].cleared, False)
                self.assertEqual(errors[0].msg, str(msg))
                self.assertEqual(errors[0].code, msg.code)

                qs = GanetiError.objects.filter(cleared=True)
                cleared = qs.get_errors(obj=i)
                self.assertEqual(0, len(cleared))

        # set all errors as cleared  and test if it was a success
        for i in (cluster0, cluster1):
            GanetiError.objects.clear_errors(obj=i)

            qs = GanetiError.objects.filter(cleared=True)
            cleared = qs.get_errors(obj=i)
            self.assertEqual(2, len(cleared))
            self.assertEqual(cleared[0].cleared, True)
            self.assertEqual(cleared[1].cleared, True)
            self.assertEqual(cleared[0].msg, str(msg))
            self.assertEqual(cleared[1].msg, str(msg))
            self.assertEqual(cleared[0].code, msg.code)
            self.assertEqual(cleared[1].code, msg.code)

        for i in (vm0, vm1):
            GanetiError.objects.clear_errors(obj=i.cluster)

            qs = GanetiError.objects.filter(cleared=True)
            cleared = qs.get_errors(obj=i.cluster)
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


class TestErrorViews(TestGanetiErrorBase, TestCase):

    def setUp(self):
        super(TestErrorViews, self).setUp()

        user = User(id=2, username='tester0')
        user.set_password('secret')
        user.save()

        self.user = user
        self.cluster = self.create_model(Cluster, hostname="test0",
                                         slug="OSL_TEST0")
        self.vm = self.create_model(VirtualMachine, cluster=self.cluster,
                                    hostname="vm0.test.org")
        self.c = Client()

    def tearDown(self):
        super(TestErrorViews, self).tearDown()
        User.objects.all().delete()

    def test_clear_error(self):
        url = '/error/clear/%s'

        msg = client.GanetiApiError("Simulating an error", 777)
        RapiProxy.error = msg

        # test store_error
        store_error = GanetiError.store_error
        c_error = store_error(str(msg), obj=self.cluster, code=msg.code)
        c_error = GanetiError.objects.get(pk=c_error.pk)
        self.assertFalse(c_error.cleared)

        vm_error = store_error(str(msg), obj=self.vm, code=msg.code)
        vm_error = GanetiError.objects.get(pk=vm_error.pk)
        self.assertFalse(vm_error.cleared)

        # anonymous user
        response = self.c.post(url % vm_error.id, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        vm_error = GanetiError.objects.get(pk=vm_error.pk)
        self.assertFalse(vm_error.cleared)

        # unauthorized user
        self.assertTrue(self.c.login(username=self.user.username,
                                     password='secret'))
        response = self.c.post(url % vm_error.id)
        self.assertEqual(403, response.status_code)
        vm_error = GanetiError.objects.get(pk=vm_error.pk)
        self.assertFalse(vm_error.cleared)

        # nonexisent error
        response = self.c.post(url % -1)
        self.assertEqual(404, response.status_code)

        # authorized for cluster (cluster admin)
        self.user.grant('admin', self.cluster)
        response = self.c.post(url % c_error.id)
        self.assertEqual(200, response.status_code)
        c_error = GanetiError.objects.get(pk=c_error.pk)
        self.assertTrue(c_error.cleared)
        GanetiError.objects.all().update(cleared=False)

        # authorized for vm (cluster admin)
        response = self.c.post(url % vm_error.id)
        self.assertEqual(200, response.status_code)
        vm_error = GanetiError.objects.get(pk=vm_error.pk)
        self.assertTrue(vm_error.cleared)
        GanetiError.objects.all().update(cleared=False)
        self.user.revoke_all(self.cluster)

        # authorized for vm (vm owner)
        self.vm.owner = self.user.get_profile()
        self.vm.save()
        response = self.c.post(url % vm_error.id)
        self.assertEqual(200, response.status_code)
        vm_error = GanetiError.objects.get(pk=vm_error.pk)
        self.assertTrue(vm_error.cleared)
        GanetiError.objects.all().update(cleared=False)
        self.vm.owner = None
        self.vm.save()

        # authorized for vm (superuser)
        self.user.is_superuser = True
        self.user.save()
        response = self.c.post(url % vm_error.id)
        self.assertEqual(200, response.status_code)
        vm_error = GanetiError.objects.get(pk=vm_error.pk)
        self.assertTrue(vm_error.cleared)
        GanetiError.objects.all().update(cleared=False)
