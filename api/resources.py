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
from django.core.paginator import Page
from tastypie.utils.urls import trailing_slash


__author__ = 'bojan'

from tastypie.resources import ModelResource, Resource, HttpAccepted, HttpBadRequest, HttpApplicationError, HttpCreated, HttpResponseNotFound, ResourceOptions
from sets import Set
from tastypie.fields import ForeignKey
from django.contrib.auth.models import User
from ganeti_web.models import VirtualMachine, SSHKey, Cluster, Node, CachedClusterObject, Job, ClusterUser
from tastypie import fields
from tastypie.authentication import Authentication, BasicAuthentication, ApiKeyAuthentication
from tastypie.authorization import Authorization, DjangoAuthorization
from tastypie.bundle import Bundle
from tastypie.exceptions import NotFound
from authorization import SuperuserAuthorization
from django.http import HttpRequest, HttpResponse
import ganeti_web.views.users
from django import forms
from tastypie.validation import Validation, FormValidation
from django.contrib.auth.forms import UserCreationForm
from tastypie.utils.dict import dict_strip_unicode_keys
from api.validation import UserValidation
from ganeti_web.views.general import overview
from django.core.context_processors import request
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from tastypie.http import HttpMultipleChoices, HttpGone
from ganeti_web.views.cluster import list_, detail
from ganeti_web.views.virtual_machine import list_
from ganeti_web.views.jobs import status, detail, clear
from tastypie.models import ApiKey
import ganeti_web.views.jobs
import ganeti_web.views.node
import ganeti_web.views.virtual_machine
from ganeti_web.views.general import get_used_resources, used_resources

class UserResource(ModelResource):
    """
    Defines user resource, providing ssh_keys additionally
    """
    class Meta:
        queryset = User.objects.all()
        resource_name = 'user'
        allowed_methods = ['get', 'put', 'post', 'delete']
        authentication = ApiKeyAuthentication()
        authorization = SuperuserAuthorization()
        validation = UserValidation()


    def dehydrate(self, bundle):
        ssh_keys = []
        for key in SSHKey.objects.filter(user__pk=bundle.obj.id):
            ssh_keys.append(key.key)
        bundle.data['ssh_keys'] = ssh_keys
        bundle.data['api_key'] = ApiKey.objects.get(user__pk=bundle.obj.id).key
        return bundle

    def put_detail(self, request, **kwargs):
        try:
            deserialized = self.deserialize(request, request.raw_post_data, format=request.META.get('CONTENT_TYPE', 'application/json'))
        except (Exception):
            return HttpBadRequest()
        deserialized = self.alter_deserialized_detail_data(request, deserialized)
        bundle = self.build_bundle(data=dict_strip_unicode_keys(deserialized))
        self.is_valid(bundle, request)
        if (bundle.data.has_key('api_key')):
            return HttpBadRequest()
        updated_bundle = self.obj_update(bundle, request=request, pk=kwargs.get('pk'))
        return HttpAccepted

    def post_list(self, request, **kwargs):
        print "post"
        try:
            deserialized = self.deserialize(request, request.raw_post_data, format=request.META.get('CONTENT_TYPE', 'application/json'))
        except (Exception):
            return HttpBadRequest()
        deserialized = self.alter_deserialized_detail_data(request, deserialized)
        bundle = self.build_bundle(data=dict_strip_unicode_keys(deserialized))

        # action: generate api key for particular user
        if (bundle.data.has_key('action')) & (bundle.data.get('action')=='generate_api_key') & (bundle.data.has_key('userid')):
            api_key = None
            try:
                api_key = ApiKey.objects.get(user=bundle.data.get('userid'))
                api_key.key = api_key.generate_key()
                api_key.save()
            except ApiKey.DoesNotExist:
                api_key = ApiKey.objects.create(user=bundle.data.get('userid'))

            # return created key info
            if (api_key != None):
                bun = Bundle()
                bun.data['userid'] = bundle.data.get('userid')
                bun.data['api_key'] = api_key.key
                return HttpResponse(status=201, content=self.serialize(request, bun, self.determine_format(request)))
        return HttpResponse(status=200)


class SSHKeyResource(ModelResource):
    """
    Defines ssh key resource, providing user_id additionally
    """
    user = fields.ToOneField(UserResource, 'user')
    class Meta:
        queryset = SSHKey.objects.all()
        resource_name = 'ssh_key'
        allowed_methods = ['get']
        authentication = ApiKeyAuthentication()
        authorization = SuperuserAuthorization()



class CachedCluster(ModelResource):
    class Meta:
        object_class = CachedClusterObject
        #queryset = CachedClusterObject.objects.all()
        resource_name='cco'



class ClusterResource(ModelResource):
    
    class Meta:
        resource_name = 'cluster'
        object_class = Cluster
        allowed_methods=['get']
        queryset = Cluster.objects.all()
        fields = ['username','id', 'disk', 'description','hostname', 'ram','slug','port','virtual_cpus','slug']

    def dehydrate(self, bundle):
        bundle.data['software_version'] = bundle.obj.info['software_version']
        bundle.data['default_hypervisor'] = bundle.obj.info['default_hypervisor']
        bundle.data['master'] = bundle.obj.info['master']
        bundle.data['nodes_count'] = bundle.obj.nodes.count()
        bundle.data['vm_count'] = bundle.obj.virtual_machines.count()
        return bundle

    def get_detail(self, request, **kwargs):
        print kwargs
        obj = Bundle()
        try:
           obj = self.cached_obj_get(request=request, **self.remove_api_resource_names(kwargs))
        except ObjectDoesNotExist:
           return HttpResponseNotFound()
        except MultipleObjectsReturned:
           return HttpMultipleChoices("More than one resource is found at this URI.")

        bundle = self.full_dehydrate(obj)
        bundle = self.alter_detail_data_to_serialize(request, bundle)
        bundle.data['info'] = bundle.obj.info
        bundle.data['quota'] = bundle.obj.get_quota(user=User.objects.get(username=request.META['USER']).id if (request.META.has_key("USER")) else None)
        bundle.data['default_quota'] = bundle.obj.get_default_quota()
        bundle.data['available_ram'] = bundle.obj.available_ram
        bundle.data['available_disk'] = bundle.obj.available_disk
        bundle.data['missing_db'] = bundle.obj.missing_in_db
        bundle.data['missing_ganeti'] = bundle.obj.missing_in_ganeti
        bundle.data['nodes_missing_db'] = bundle.obj.nodes_missing_in_db
        bundle.data['nodes_missing_ganeti'] = bundle.obj.nodes_missing_in_ganeti
        return self.create_response(request, bundle)

    def get_object_list(self, request):
        objects = Cluster.objects.all()
        return objects

    def obj_get_list(self, request=None, **kwargs):
        return self.get_object_list(request)



class VMResource(ModelResource):
    cluster = fields.ForeignKey('api.resources.ClusterResource', 'cluster', full=False, null=True)
    primary_node = fields.ForeignKey('api.resources.NodeResource', 'primary_node', full=False, null=True)
    secondary_node = fields.ForeignKey('api.resources.NodeResource', 'secondary_node', full=False, null=True)
    last_job = fields.ForeignKey('api.resources.JobResource', 'last_job', full=False, null=True)
    
    class Meta:
        queryset = VirtualMachine.objects.all()
        object_class = VirtualMachine
        resource_name = 'vm'
        allowed_methods = ['get']
        fields = {'slug','cluster', 'id', 'ram','disk_size','hostname','operating_system', 'virtual_cpus','status', 'pending_delete', 'deleted'}

    def dehydrate(self, bundle):
        vm = bundle.obj
        vm_detail = ganeti_web.views.virtual_machine.detail(bundle.request, vm.cluster.slug, vm.hostname, True)
        bundle.data['admin'] = vm_detail['admin']
        bundle.data['cluster_admin'] = vm_detail['cluster_admin']
        bundle.data['remove'] = vm_detail['remove']
        bundle.data['power'] = vm_detail['power']
        bundle.data['modify'] = vm_detail['modify']
        bundle.data['migrate'] = vm_detail['migrate']
        if (vm_detail.has_key('job')):
            bundle.data['job'] = vm_detail['job']
        return bundle

    def obj_get(self, request=None, **kwargs):
        vm = super(VMResource, self).obj_get(request=request, **kwargs)
        vm_detail = ganeti_web.views.virtual_machine.detail(request, vm.cluster.slug, vm.hostname, True)
        print vm_detail
        return vm_detail['instance']


    def obj_get_list(self, request=None, **kwargs):
        vms = list_(request, True)
        return vms 



class ClusterUserResource(ModelResource):

    class Meta:
        queryset = ClusterUser.objects.all()
        object_class = ClusterUser
        resource_name = 'cluster_user'
        allowed_methods = ['get']
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()


    def dehydrate(self, bundle):
        cluster_user = bundle.obj
        x = cluster_user.used_resources()
        ug = {}
        for y in x:
            vm = VirtualMachine.objects.get(pk=y)
            ug[vm.hostname]=x[y] # TODO integrate vm with link relation
        bundle.data['vms'] = ug
        return bundle

class NodeResource(ModelResource):
    cluster = fields.ForeignKey(ClusterResource, 'cluster', full=False, null=True)
    last_job = fields.ForeignKey('api.resource.JobResource', 'last_job', full=False, null=True)

    # TODO: Node actions: migrate, evacuate, role

    class Meta:
        queryset = Node.objects.all()
        object_class = Node
        resource_name = 'node'
        allowed_methods = ['get']
        fields = {'ram_total', 'ram_free', 'disk_total', 'disk_free', 'role', 'offline', 'id'}
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()

    def dehydrate(self, bundle):
        node = bundle.obj
        node_detail = ganeti_web.views.node.detail(bundle.request, node.cluster.slug, node.hostname, True)
        bundle.data['cluster'] = node_detail['cluster']
        bundle.data['node_count'] = node_detail['node_count']
        bundle.data['admin'] = node_detail['admin']
        bundle.data['modify'] = node_detail['modify']
        bundle.data['info'] = node_detail['node'].info
        bundle.data['hostname'] = node_detail['node'].hostname
        return bundle


    def obj_get(self, request=None, **kwargs):
        node = super(NodeResource, self).obj_get(request, **kwargs)
        node_detail = ganeti_web.views.node.detail(request, node.cluster.slug, node.hostname, True)
        return node_detail['node']


class JobResource(ModelResource):
    cluster = fields.ForeignKey(ClusterResource, 'cluster', full=False)

    def dehydrate(self, bundle):
        job = bundle.obj
        job_detail = ganeti_web.views.jobs.detail(bundle.request, job.cluster.slug, job.job_id, True)
        bundle.data['opresult'] = bundle.obj.info['opresult']
        bundle.data['summary'] = bundle.obj.info['summary']
        bundle.data['ops'] = bundle.obj.info['ops']
        bundle.data['cluster_admin'] = job_detail['cluster_admin']
        print bundle.obj.info
        return bundle

    class Meta:
        queryset = Job.objects.all()
        object_class = Job
        resource_name = 'job'
        allowed_methods = ['get', 'delete']
        fields = {'status', 'finished', 'job_id', 'cleared'}
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()

    def obj_get(self, request, **kwargs):
        print "?KWARGS?"
        print kwargs
        job = super(JobResource, self).obj_get(request, **kwargs)
        job_status = status(request, job.cluster.slug, job.job_id, True)
        return job_status

    def obj_delete(self, request, **kwargs):
        try:
            job = self.obj_get(request, **kwargs)
        except NotFound:
            raise NotFound("Object not found")
        print job.info
        res = clear(request, job.cluster.slug, job.job_id, True)
        if (res):
            job.delete()

