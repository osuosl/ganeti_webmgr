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

from ganeti_web import models
from ganeti_web.models import Cluster, VirtualMachineTemplate, VirtualMachine
from ganeti_web.tests.rapi_proxy import INSTANCE, RapiProxy


__all__ = ('TestTemplateViews', )


class TestTemplateViews(TestCase, ViewTestMixin, UserTestMixin):
    """
    Test the views for VirtualMachineTemplates
    """
    def setUp(self):
        self.tearDown()
        models.client.GanetiRapiClient = RapiProxy

        cluster = Cluster(hostname='test.cluster', slug='test', username='tester', password='secret')
        cluster.id = 23 # XXX MySQL DB does not reset auto-increment IDs when an object is removed
        cluster.save()
        cluster.sync_nodes()

        template = VirtualMachineTemplate(template_name="Template1", cluster=cluster)
        template.disks = []
        template.nics = []
        template.save()

        instance = VirtualMachine(hostname='new.vm.hostname', cluster=cluster)
        instance.info = INSTANCE
        instance.disks = []
        instance.nics = []
        instance.save()

        # Users
        self.create_users([
            ('superuser', {'is_superuser':True}),
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
            disk_template = 'plain',
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
        args = (self.cluster.slug,self.template)
        self.assert_standard_fails(url, args, authorized=False)

    def test_create_view(self):
        """
        Test creating a new virtual machine template through the view.
        """
        url = '/template/create/'
        args = ()
        self.assert_standard_fails(url, args, authorized=False)

        # GET
        self.assert_200(url, args,
            users = [self.unauthorized],
            template='ganeti/vm_template/create.html')

        def test_exist(user, request):
            self.assertTrue(VirtualMachineTemplate.objects.filter(
                template_name=self.create_template_data['template_name']).exists())
        # POST
        self.assertFalse(VirtualMachineTemplate.objects.filter(
            template_name=self.create_template_data['template_name']).exists())
        self.assert_200(url, args, method='post',
            users=[self.superuser, self.cluster_admin, self.create_vm],
            data=self.create_template_data,
            follow=True,
            setup=True,
            tests=test_exist,
            template='ganeti/vm_template/detail.html')

        # unauthorized user (User with no cluster access)
        VirtualMachineTemplate.objects.all().delete()
        self.assertTrue(self.c.login(username=self.unauthorized.username, password='secret'))
        request = self.c.post(url % args, self.create_template_data)
        self.assertEqual(200, request.status_code)
        self.assertTemplateUsed(request, 'ganeti/vm_template/create.html')
        form = request.context['form']
        self.assertEqual(['cluster'], form.errors.keys())

        self.assertFalse(VirtualMachineTemplate.objects.filter(
            template_name=self.create_template_data['template_name']).exists())

    def test_create_instance_from_template_view(self):
        """
        Tests creating an instance from a template
        """
        url = '/cluster/%s/template/%s/vm/'
        args = (self.cluster.slug, self.template)

        # GET
        self.assert_200(url, args,
            users = [self.superuser, self.cluster_admin, self.create_vm],
            template='ganeti/virtual_machine/create.html')

    def test_delete_view(self):
        """
        Test deleting a template using the view
        """
        url = '/cluster/%s/template/%s/delete/'
        args = (self.cluster.slug, self.template)

        self.assertTrue(VirtualMachineTemplate.objects.filter(pk=self.template.pk).exists())
        self.assert_401(url, args)
        self.assert_401(url, args, method='delete')
        self.assertTrue(VirtualMachineTemplate.objects.filter(pk=self.template.pk).exists())

        def test_exist(user, request):
            self.assertFalse(VirtualMachineTemplate.objects.filter(pk=self.template.pk).exists())

        self.assert_200(url, args, users=[self.superuser, self.cluster_admin,
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
            users = [self.superuser, self.create_vm, self.cluster_admin],
            template='ganeti/vm_template/copy.html')
        self.assert_403(url, args,
            users = [self.unauthorized])

        def test_name(user, request):
            self.assertTrue(VirtualMachineTemplate.objects.filter(template_name='asdf').exists())
        # POST
        self.assert_200(url, args, method='post',
            users=[self.superuser, self.cluster_admin, self.create_vm],
            data={'template_name':'asdf'},
            setup=True,
            follow=True,
            tests=test_name,
            template='ganeti/vm_template/detail.html')

        self.assert_403(url, args, method='post',
            data={'template_name':'asdfff'},
            users=[self.unauthorized])
        self.assertFalse(VirtualMachineTemplate.objects.filter(template_name='asdfff').exists())

    def test_edit_view(self):
        """
        Test editing a template
        """
        url = '/cluster/%s/template/%s/edit/'
        args = (self.cluster.slug, self.template)
        self.assert_standard_fails(url, args)

        # GET
        self.assert_200(url, args,
            users = [self.superuser, self.create_vm, self.cluster_admin],
            template='ganeti/vm_template/create.html')
        self.assert_403(url, args,
            users = [self.unauthorized])

        # POST
        data_=self.create_template_data.copy()
        update = dict(
            vcpus=4,
        )
        data_.update(update)
        def test_vcpus(user, request):
            vm = VirtualMachineTemplate.objects.get(pk=self.template.pk)
            self.assertEqual(4, vm.vcpus)

        self.assertTrue(VirtualMachineTemplate.objects.filter(pk=self.template.pk).exists())
        self.assert_200(url, args, method='post',
            users=[self.superuser, self.cluster_admin, self.create_vm],
            data=data_,
            setup=True,
            follow=True,
            tests=test_vcpus,
            template='ganeti/vm_template/detail.html')

        self.assert_403(url, args, method='post',
            data=data_,
            users=[self.unauthorized])

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

        # Copied from create_template_from_instance view
        # TODO figure out good way to associate the keys
        #  of VirtualMachine to VirtualMachineTemplate
        info = self.instance.info
        links = info['nic.links']
        modes = info['nic.modes']
        sizes = info['disk.sizes']

        data = dict(
            template_name=self.instance.hostname,
            cluster=self.cluster.id,
            start=info['admin_state'],
            disk_template=info['disk_template'],
            disk_type=info['hvparams']['disk_type'],
            nic_type=info['hvparams']['nic_type'],
            os=self.instance.operating_system,
            vcpus=self.instance.virtual_cpus,
            memory=self.instance.ram,
            disks=[{'size':size} for size in sizes],
            nics=[{'mode':mode, 'link':link} for mode, link in zip(modes, links)],
            nic_count=len(links),
        )

        def test_fields(user, response):
            self.assertContains(response, self.instance)
            form = response.context['form']
            for field in data:
                self.assertEqual(data[field], form.initial[field])

        # GET
        self.assert_200(url, args,
            users = [self.superuser, self.create_vm, self.cluster_admin],
            tests = test_fields,
            template='ganeti/vm_template/create.html')
        self.assert_403(url, args,
            users = [self.unauthorized])

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

        # Copied from create_instance_from_template
        data = dict(
            hostname=self.template.template_name,
            cluster=self.template.cluster_id,
        )
        data.update(vars(self.template))
        ignore_fields = ('disks', '_state', 'pnode', 'snode',
            'description', '_cluster_cache')
        for field in ignore_fields:
            del data[field]
        data['disk_count'] = len(self.template.disks)
        for i,disk in enumerate(self.template.disks):
            data['disk_size_%s'%i] = disk['size']

        def test_fields(user, response):
            self.assertContains(response, self.template)
            form = response.context['form']
            for field in data:
                self.assertEqual(data[field], form.initial[field])

        # GET
        self.assert_200(url, args,
            users = [self.superuser, self.create_vm, self.cluster_admin],
            tests = test_fields,
            template='ganeti/virtual_machine/create.html')
        self.assert_403(url, args,
            users = [self.unauthorized])

