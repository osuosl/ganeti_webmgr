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

from django_test_tools.users import UserTestMixin
from django_test_tools.views import ViewTestMixin

from ganeti_web.models import Cluster, VirtualMachineTemplate


__all__ = ('TestTemplateViews', )

global user, user1, group, cluster_admin, superuser
global cluster, c

class TestTemplateViews(TestCase, ViewTestMixin, UserTestMixin):
    """
    Test the views for VirtualMachineTemplates
    """
    def setUp(self):
        self.tearDown()

        cluster1 = Cluster(hostname='test.cluster', slug='test')
        cluster1.save()
        template1 = VirtualMachineTemplate(template_name="Template1")
        template1.cluster = cluster1
        template1.save()

        dict_ = globals()
        dict_['template1'] = template1
        dict_['cluster'] = cluster1

    def tearDown(self):
        VirtualMachineTemplate.objects.all().delete()
    
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
        args = (cluster.slug,template1)
        self.assert_standard_fails(url, args, authorized=False)

    def test_create_view(self):
        """
        Test creating a new virtual machine template through the view.
        """
        url = '/template/create'
        args = ()
        self.assert_standard_fails(url, args, authorized=False)
