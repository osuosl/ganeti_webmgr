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
from django.test.client import Client
from django.contrib.auth.models import User

from django_test_tools.users import UserTestMixin
from django_test_tools.views import ViewTestMixin

from clusters.models import Cluster
from virtualmachines.models import VirtualMachine
from vm_templates.models import VirtualMachineTemplate

from utils import client
from utils.proxy import RapiProxy
from utils.proxy.constants import INSTANCE


__all__ = ('TestTemplateViews', )


class TestTemplateViews(TestCase, ViewTestMixin, UserTestMixin):
    """
    Test the views for VirtualMachineTemplates
    """
    def setUp(self):
        self.tearDown()
        client.GanetiRapiClient = RapiProxy

        cluster = Cluster(hostname='test.cluster', slug='test',
                          username='tester', password='secret')
        cluster.id = 23  # XXX MySQL DB does not reset auto-increment
                         # IDs when an object is removed
        cluster.save()
        cluster.sync_nodes()

        template = VirtualMachineTemplate(template_name="Template1",
                                          cluster=cluster)
        template.disks = [{'size': 500}]
        template.nics = [{'mode': 'bridged', 'link': ''}]
        template.save()

        instance = VirtualMachine(hostname='new.vm.hostname', cluster=cluster)
        instance.info = INSTANCE
        instance.disks = []
        instance.nics = []
        instance.save()

        # Users
        self.create_users([
            ('superuser', {'is_superuser': True}),
            'cluster_admin',
            'create_vm',
            'unauthorized',
        ])
        self.cluster_admin.grant('admin', cluster)
        self.create_vm.grant('create_vm', cluster)

        self.create_template_data = dict(
            cluster=cluster.pk,
            template_name='foo_bar',
            memory=512,
            disk_template='plain',
            disk_count=0,
            nic_count=0,
        )

        self.cluster = cluster
        self.template = template
        self.instance = instance
        self.c = Client()

    def tearDown(self):
        VirtualMachineTemplate.objects.all().delete()
        VirtualMachine.objects.all().delete()
        Cluster.objects.all().delete()
        User.objects.all().delete()

    def test_list_view(self):
        """
        Test viewing a list of virtual machine templates.
        """
        url = '/templates/'
        args = ()
        self.assert_standard_fails(url, args, authorized=False)

    def test_detail_view(self):
        """
        Test viewing details of a virtual machine template.
        """
        url = '/cluster/%s/template/%s'
        args = (self.cluster.slug, self.template)
        self.assert_standard_fails(url, args, authorized=False)

    def test_create_instance_from_template_view(self):
        """
        Tests creating an instance from a template
        """
        url = '/cluster/%s/template/%s/vm/'
        args = (self.cluster.slug, self.template)

        # GET
        self.assert_200(url, args,
                        users=[self.superuser, self.cluster_admin,
                               self.create_vm],
                        template='ganeti/vm_template/to_vm.html')

    def test_delete_view(self):
        """
        Test deleting a template using the view
        """
        url = '/cluster/%s/template/%s/delete/'
        args = (self.cluster.slug, self.template)

        self.assertTrue(
            VirtualMachineTemplate.objects.filter(
                pk=self.template.pk).exists())
        self.assert_401(url, args)
        self.assert_401(url, args, method='delete')
        self.assertTrue(
            VirtualMachineTemplate.objects.filter(
                pk=self.template.pk).exists())

        def test_exist(user, request):
            self.assertFalse(
                VirtualMachineTemplate.objects.filter(
                    pk=self.template.pk).exists())

        self.assert_200(url, args,
                        users=[self.superuser, self.cluster_admin,
                               self.create_vm],
                        method='delete',
                        setup=True,
                        tests=test_exist,
                        mime='application/json')

        self.assert_403(url, args, users=[self.unauthorized],
                        method='delete')

    def test_copy_view(self):
        """
        Test creating a copy of a template
        """
        url = '/cluster/%s/template/%s/copy/'
        args = (self.cluster.slug, self.template)
        self.assert_standard_fails(url, args, authorized=False)

        # GET
        self.assert_200(url, args,
                        users=[self.superuser, self.create_vm,
                               self.cluster_admin],
                        template='ganeti/vm_template/copy.html')
        self.assert_403(url, args,
                        users=[self.unauthorized])

        def test_name(user, request):
            self.assertTrue(
                VirtualMachineTemplate.objects.filter(
                    template_name='asdf').exists())
        # POST
        self.assert_200(url, args, method='post',
                        users=[self.superuser, self.cluster_admin,
                               self.create_vm],
                        data={'template_name': 'asdf'},
                        setup=True,
                        follow=True,
                        tests=test_name,
                        template='ganeti/vm_template/detail.html')

        self.assert_403(url, args, method='post',
                        data={'template_name': 'asdfff'},
                        users=[self.unauthorized])
        self.assertFalse(
            VirtualMachineTemplate.objects.filter(
                template_name='asdfff').exists())

    def test_create_template_from_instance(self):
        """
        Test the create_template_from_instance view

        Verifies:
            * Only users authorized are able to view page
            * Correct fields are set on the template
        """
        url = '/cluster/%s/%s/template/'
        args = (self.cluster.slug, self.instance)
        self.assert_standard_fails(url, args)

        # GET
        self.assert_200(url, args,
                        users=[self.superuser, self.create_vm,
                               self.cluster_admin],
                        template='ganeti/vm_template/to_instance.html')
        self.assert_403(url, args,
                        users=[self.unauthorized])

    def test_create_instance_from_template(self):
        """
        Test the create_instance_from_template view

        Verifies:
            * Only authorized users are able to access view
            * Correct fields are set on the template
        """
        url = '/cluster/%s/template/%s/vm/'
        args = (self.cluster.slug, self.template)
        self.assert_standard_fails(url, args)

        # GET
        self.assert_200(url, args,
                        users=[self.superuser, self.create_vm,
                               self.cluster_admin],
                        template='ganeti/vm_template/to_vm.html')

        self.assert_403(url, args,
                        users=[self.unauthorized])
