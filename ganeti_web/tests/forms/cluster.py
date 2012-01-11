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


from django.test import TestCase
from ganeti_web.forms.cluster import EditClusterForm

from ganeti_web.tests.rapi_proxy import RapiProxy
from ganeti_web import models
Cluster = models.Cluster
VirtualMachine = models.VirtualMachine
Node = models.Node
Quota = models.Quota


__all__ = ['TestClusterFormNew', 'TestClusterFormEdit']


class TestClusterFormBase(TestCase):

    def setUp(self):
        self.tearDown()
        models.client.GanetiRapiClient = RapiProxy

        self.cluster = Cluster(hostname='test.osuosl.test', slug='OSL_TEST')
        self.cluster.save()

        self.data = dict(hostname='new-host3.hostname',
                    slug='new-host3',
                    port=5080,
                    description='testing editing clusters',
                    username='tester',
                    password = 'secret',
                    virtual_cpus=1,
                    disk=2,
                    ram=3
                    )

    def tearDown(self):
        VirtualMachine.objects.all().delete()
        Quota.objects.all().delete()
        Cluster.objects.all().delete()


class TestClusterFormNew(TestClusterFormBase):

    def test_unbound(self):
        form = EditClusterForm()

    def test_bound(self):
        form = EditClusterForm(self.data)
        self.assertTrue(form.is_valid())

    def test_required_fields(self):
        """
        Tests adding a new cluster
        """
        data = self.data
        required = ['hostname', 'port']
        for property in required:
            data_ = data.copy()
            del data_[property]
            form = EditClusterForm(data_)
            self.assertFalse(form.is_valid())

    def test_optional_fields(self):
        data = self.data
        non_required = ['slug','description','virtual_cpus','disk','ram']
        for property in non_required:
            data_ = data.copy()
            del data_[property]
            form = EditClusterForm(data_)
            self.assertTrue(form.is_valid())
            cluster = form.save()
            for k, v in data_.items():
                self.assertEqual(v, getattr(cluster, k))
            Cluster.objects.all().delete()

    def test_read_only(self):
        """ success without username or password """
        data_ = self.data
        del data_['username']
        del data_['password']
        form = EditClusterForm(data_)
        self.assertTrue(form.is_valid())
        cluster = form.save()
        for k, v in data_.items():
            self.assertEqual(v, getattr(cluster, k))

    def test_password_required(self):
        """ if either username or password are entered both are required """
        relation = ['username', 'password']
        for property in relation:
            data_ = self.data.copy()
            del data_[property]
            form = EditClusterForm(data_)
            self.assertFalse(form.is_valid())

    def test_unique_fields(self):
        # test unique fields
        form = EditClusterForm(self.data)
        form.is_valid()
        form.save()
        for property in ['hostname','slug']:
            data_ = self.data.copy()
            data_[property] = 'different'
            form = EditClusterForm(data_)
            self.assertFalse(form.is_valid())


class TestClusterFormEdit(TestClusterFormBase):


    def test_bound_form(self):
        """ tests binding form with existing instance """
        form = EditClusterForm(self.data)
        self.assertTrue(form.is_valid())

    def test_valid_edit(self):
        """
        successfully edit a cluster
        """
        data = self.data
        form = EditClusterForm(data, instance=self.cluster)
        self.assertTrue(form.is_valid())
        cluster = form.save()
        for k, v in data.items():
            self.assertEqual(v, getattr(cluster, k))

    def test_no_username_or_password_for_read_only(self):
        """
        tests that username and password are optional for read only cluster
        """
        data = self.data
        del data['username']
        del data['password']
        form = EditClusterForm(data, instance=self.cluster)
        self.assertTrue(form.is_valid())
        cluster = form.save()
        self.assertEqual('', cluster.username)
        self.assertEqual('', cluster.password)

    def test_no_password_for_writeable(self):
        """
        Tests that password is not required when the cluster already has the
        password available.  assumes username is the same
        """
        self.cluster.username = 'tester'
        self.cluster.password = 'secret'
        self.cluster.save()

        data = self.data
        del data['password']
        form = EditClusterForm(data, instance=self.cluster)
        self.assertTrue(form.is_valid())
        cluster = form.save()
        self.assertEqual('tester', cluster.username)
        self.assertEqual('secret', cluster.password)

    def test_no_password_for_writeable_new_username(self):
        """
        tests that the password is required when the username has changed
        """
        self.cluster.username = 'foo'
        self.cluster.password = 'bar'
        self.cluster.save()

        data = self.data
        del data['password']
        data['username'] = 'different'
        form = EditClusterForm(data, instance=self.cluster)
        self.assertFalse(form.is_valid())

    def test_username_required_for_writeable_new_password(self):
        """
        if password is entered for a cluster, username is required always
        """
        self.cluster.username = 'foo'
        self.cluster.password = 'bar'
        self.cluster.save()

        data = self.data
        del data['username']
        form = EditClusterForm(data, instance=self.cluster)
        self.assertFalse(form.is_valid())

    def test_username_and_password_change(self):
        """
        tests changing the password for a cluster that already had username and
        password set
        """
        self.cluster.username = 'foo'
        self.cluster.password = 'bar'
        self.cluster.save()

        data = self.data
        form = EditClusterForm(data, instance=self.cluster)
        self.assertTrue(form.is_valid())
        cluster = form.save()

        self.assertEqual('tester', cluster.username)
        self.assertEqual('secret', cluster.password)

    def test_username_and_password_added(self):
        """
        tests setting a username and password for a cluster that did not
        previously have a username and password
        """
        self.cluster.username = None
        self.cluster.password = None
        self.cluster.save()

        data = self.data
        data['username'] = 'foo'
        data['password'] = 'bar'
        form = EditClusterForm(data, instance=self.cluster)
        self.assertTrue(form.is_valid())

        cluster = form.save()
        self.assertEqual('foo', cluster.username)
        self.assertEqual('bar', cluster.password)
