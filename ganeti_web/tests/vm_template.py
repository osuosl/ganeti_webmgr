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

from ganeti_web.models import Cluster, VirtualMachineTemplate
from ganeti_web.tests.rapi_proxy import INFO


__all__ = ('TestTemplateViews', )

global unauthorized, create_vm, cluster_admin, superuser
global template, cluster, c

class TestTemplateViews(TestCase, ViewTestMixin, UserTestMixin):
    """
    Test the views for VirtualMachineTemplates
    """

    create_template_data = dict(
        template_name='foo_bar',
        memory=512,
        #TODO: Make sure form does not require at least 1 vcpu when they 
        #  are not required at all
        vcpus=1,
        )

    def setUp(self):
        self.tearDown()

        cluster = Cluster(hostname='test.cluster', slug='test')
        cluster.info = INFO
        cluster.save()
        template = VirtualMachineTemplate(template_name="Template1")
        template.cluster = cluster
        template.save()

        # unathorized and superuser added to globals 
        self.create_users([
            ('superuser', {'is_superuser':True}), 
            'unauthorized',
            'cluster_admin',
            'create_vm'
            ], globals())
        cluster_admin.grant('admin', cluster)
        create_vm.grant('create_vm', cluster)

        self.create_template_data['cluster'] = cluster.pk

        context = dict(
            cluster=cluster,
            template=template,
            c=Client()
        )
        globals().update(context)

    def tearDown(self):
        VirtualMachineTemplate.objects.all().delete()
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
        args = (cluster.slug,template)
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
            users = [unauthorized],
            template='ganeti/vm_template/create.html')

        def test_exist(user, request):
            self.assertTrue(VirtualMachineTemplate.objects.filter(
                template_name=self.create_template_data['template_name']).exists())
        # POST
        self.assertFalse(VirtualMachineTemplate.objects.filter(
            template_name=self.create_template_data['template_name']).exists())
        self.assert_200(url, args, method='post',
            users=[superuser, cluster_admin, create_vm],
            data=self.create_template_data,
            follow=True,
            setup=True,
            tests=test_exist,
            template='ganeti/vm_template/detail.html')

        # unauthorized user (User with no cluster access)
        VirtualMachineTemplate.objects.all().delete()
        self.assertTrue(c.login(username=unauthorized.username, password='secret'))
        request = c.post(url % args, self.create_template_data)
        self.assertEqual(200, request.status_code)
        self.assertTemplateUsed(request, 'ganeti/vm_template/create.html')
        form = request.context['form']
        self.assertEqual(['cluster'], form.errors.keys())

        self.assertFalse(VirtualMachineTemplate.objects.filter(
            template_name=self.create_template_data['template_name']).exists())

    def test_delete_view(self):
        """
        Test deleting a template using the view
        """
        url = '/cluster/%s/template/%s/delete/'
        args = (cluster.slug, template)

        self.assertTrue(VirtualMachineTemplate.objects.filter(pk=template.pk).exists())
        self.assert_401(url, args)
        self.assert_401(url, args, method='delete')
        self.assertTrue(VirtualMachineTemplate.objects.filter(pk=template.pk).exists())

        def test_exist(user, request):
            self.assertFalse(VirtualMachineTemplate.objects.filter(pk=template.pk).exists())

        self.assert_200(url, args, users=[superuser, cluster_admin, create_vm], 
            method='delete',
            setup=True,
            tests=test_exist,
            mime='application/json')

        self.assert_403(url, args, users=[unauthorized], 
            method='delete')

    def test_copy_view(self):
        """
        Test creating a copy of a template
        """
        url = '/cluster/%s/template/%s/copy/'
        args = (cluster.slug, template)
        self.assert_standard_fails(url, args, authorized=False)

        # GET
        self.assert_200(url, args, 
            users = [superuser, create_vm, cluster_admin],
            template='ganeti/vm_template/copy.html')
        self.assert_403(url, args,
            users = [unauthorized])

        def test_name(user, request):
            self.assertTrue(VirtualMachineTemplate.objects.filter(template_name='asdf').exists())
        # POST
        self.assert_200(url, args, method='post',
            users=[superuser, cluster_admin, create_vm],
            data={'template_name':'asdf'},
            setup=True,
            follow=True,
            tests=test_name,
            template='ganeti/vm_template/detail.html')
    
        self.assert_403(url, args, method='post',
            data={'template_name':'asdfff'},
            users=[unauthorized])
        self.assertFalse(VirtualMachineTemplate.objects.filter(template_name='asdfff').exists())

    def test_edit_view(self):
        """
        Test editing a template
        """
        url = '/cluster/%s/template/%s/edit/'
        args = (cluster.slug, template)
        self.assert_standard_fails(url, args)

        # GET
        self.assert_200(url, args, 
            users = [superuser, create_vm, cluster_admin],
            template='ganeti/vm_template/create.html')
        self.assert_403(url, args,
            users = [unauthorized])

        # POST
        data_=self.create_template_data.copy()
        data_['vcpus'] = 4
        def test_vcpus(user, request):
            vm = VirtualMachineTemplate.objects.get(pk=template.pk)
            self.assertEqual(4, vm.vcpus)

        self.assertTrue(VirtualMachineTemplate.objects.filter(pk=template.pk).exists())
        self.assert_200(url, args, method='post',
            users=[superuser, cluster_admin, create_vm],
            data=data_,
            setup=True,
            follow=True,
            tests=test_vcpus,
            template='ganeti/vm_template/detail.html')

        self.assert_403(url, args, method='post',
            data=data_,
            users=[unauthorized])
