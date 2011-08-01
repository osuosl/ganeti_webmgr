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

__author__ = 'bojan'
from authorization import SuperuserAuthorization
import ganeti_web.views.users
import ganeti_web.views.jobs
import ganeti_web.views.node
import ganeti_web.views.virtual_machine
from object_permissions.registration import get_group_perms
import object_log.views
import ganeti_web.views.users
from ganeti_web.views.jobs import status, detail, clear
import ganeti_web.views.jobs
import ganeti_web.views.node
import ganeti_web.views.virtual_machine
import object_permissions
from tastypie.utils.dict import dict_strip_unicode_keys
from tastypie.models import ApiKey
import api.utils
import object_permissions.views.groups
import object_permissions.views.permissions
import utils
from tastypie import fields
from tastypie.authentication import Authentication, BasicAuthentication, ApiKeyAuthentication
from tastypie.authorization import Authorization, DjangoAuthorization
from tastypie.exceptions import NotFound
from django.http import HttpRequest, HttpResponse, Http404
import ganeti_web.views.users
from ganeti_web.views.virtual_machine import list_
import ganeti_web.views.jobs
import ganeti_web.views.node
import ganeti_web.views.virtual_machine
from tastypie.resources import ModelResource, Resource, HttpAccepted, HttpBadRequest, HttpApplicationError, HttpCreated, HttpResponseNotFound, ResourceOptions
from django.contrib.auth.models import User, Group
from ganeti_web.models import VirtualMachine, SSHKey, Cluster, Node, CachedClusterObject, Job, ClusterUser
from tastypie.bundle import Bundle
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from tastypie.http import HttpMultipleChoices, HttpGone, HttpNoContent

class UserResource(ModelResource):
    """
    Defines user resource, providing ssh_keys additionally
    """
    class Meta:
        queryset = User.objects.all()
        resource_name = 'user'
        allowed_methods = ['get', 'put', 'post', 'delete']
        #authentication = ApiKeyAuthentication()
        #authorization = SuperuserAuthorization()
        #validation = UserValidation()


    def dehydrate(self, bundle):
        ssh_keys = []
        for key in SSHKey.objects.filter(user__pk=bundle.obj.id):
            ssh_keys.append(key.key)
        bundle.data['ssh_keys'] = ssh_keys
        try:
            bundle.data['api_key'] = ApiKey.objects.get(user__pk=bundle.obj.id).key
        except(ApiKey.DoesNotExist):
            {}
        #cluster_user = ClusterUser.objects.get(name=bundle.obj.name)
        #perms_info = object_permissions.views.groups.all_permissions(bundle.request, bundle.data['id'], rest=True)

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

    def post_detail(self, request, **kwargs):
        print kwargs
        print kwargs.get('pk')
        try:
            deserialized = self.deserialize(request, request.raw_post_data, format=request.META.get('CONTENT_TYPE', 'application/json'))
        except (Exception):
            return HttpBadRequest()
        deserialized = self.alter_deserialized_detail_data(request, deserialized)
        bundle = self.build_bundle(data=dict_strip_unicode_keys(deserialized))

        # action: generate api key for particular user
        if (bundle.data.has_key('action')) & (bundle.data.get('action')=='generate_api_key'):
            return api.utils.generate_api_key(request, kwargs.get('pk'))

        # clean users api key
        if (bundle.data.has_key('action')) & (bundle.data.get('action')=='clean_api_key'):
            return api.utils.clean_api_key(request, kwargs.get('pk'))

        return HttpResponse(status=204)


    def post_list(self, request, **kwargs):
        try:
            deserialized = self.deserialize(request, request.raw_post_data, format=request.META.get('CONTENT_TYPE', 'application/json'))
        except (Exception):
            return HttpBadRequest()
        deserialized = self.alter_deserialized_detail_data(request, deserialized)
        bundle = self.build_bundle(data=dict_strip_unicode_keys(deserialized))

        # action: generate api key for particular user
        if (bundle.data.has_key('action')) & (bundle.data.get('action')=='generate_api_key') & (bundle.data.has_key('userid')):
            return api.utils.generate_api_key(request, bundle.data.get('userid'))

        # clean users api key
        if (bundle.data.has_key('action')) & (bundle.data.get('action')=='clean_api_key') & (bundle.data.has_key('userid')):
            return api.utils.clean_api_key(request, bundle.data.get('userid'))

        return HttpResponse(status=204)


class GroupResource(ModelResource):
    """
    Defines group resource
    """
    class Meta:
        queryset = Group.objects.all()
        resource_name = 'group'
        allowed_methods = ['get', 'put', 'post', 'delete']
        authentication = ApiKeyAuthentication()
        authorization = SuperuserAuthorization()

    def dehydrate(self, bundle):

        # permissions on virtual machines and clusters
        perms_info = object_permissions.views.groups.all_permissions(bundle.request, bundle.data['id'], rest=True)
        if (perms_info.has_key('error')):
            return bundle
        bundle.data['permissions']={'vm':[], 'cluster':[]}
        bundle.data['users']=[]
        bundle.data['used_resources']=[]
        used_resources = []
        cluster_user = ClusterUser.objects.get(name=bundle.obj.name)

        if (perms_info.has_key('perm_dict') and len(perms_info['perm_dict']) > 0):
            if (perms_info.get('perm_dict').has_key('Cluster')):
                for cl in perms_info.get('perm_dict').get('Cluster'):
                    bundle.data['permissions']['cluster'].append({'object':ClusterResource().get_resource_uri(cl), 'permissions':get_group_perms(bundle.obj, cl)})
                    used_resources.append({'object':ClusterResource().get_resource_uri(cl), 'resources_used':cluster_user.used_resources(cl,only_running = False)})

            if (perms_info.get('perm_dict').has_key('VirtualMachine')):
                for vm in perms_info.get('perm_dict').get('VirtualMachine'):
                    bundle.data['permissions']['vm'].append({'object':VMResource().get_resource_uri(vm), 'permissions':get_group_perms(bundle.obj, vm)})

        # group users
        users = User.objects.filter(groups=bundle.obj.id)
        for user in users:
            bundle.data['users'].append(UserResource().get_resource_uri(user))

        # used resources by group objects
        bundle.data['used_resources'] = used_resources

        # get log items
        log = object_log.views.list_for_group(bundle.request, bundle.obj.id, True)
        bundle.data['log'] = api.utils.extract_log_actions(bundle.request, bundle.obj.id, log)

        return bundle



class SSHKeyResource(ModelResource):
    """
    Defines ssh key resource, providing user_id additionally
    """
    print globals()
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


class VMResource(ModelResource):
    cluster = fields.ForeignKey('api.resources.ClusterResource', 'cluster', full=False, null=True)
    primary_node = fields.ForeignKey('api.resources.NodeResource', 'primary_node', full=False, null=True)
    secondary_node = fields.ForeignKey('api.resources.NodeResource', 'secondary_node', full=False, null=True)
    last_job = fields.ForeignKey('api.resources.JobResource', 'last_job', full=False, null=True)

    class Meta:
        queryset = VirtualMachine.objects.all()
        object_class = VirtualMachine
        resource_name = 'vm'
        allowed_methods = ['get','delete', 'post']
        fields = {'slug','cluster', 'id', 'ram','disk_size','hostname','operating_system', 'virtual_cpus','status', 'pending_delete', 'deleted'}
        authentication = ApiKeyAuthentication()
        authorization = DjangoAuthorization()

    def dehydrate(self, bundle):
        vm = bundle.obj
        vm_detail = ganeti_web.views.virtual_machine.detail(bundle.request, vm.cluster.slug, vm.hostname, True)
        bundle.data['admin'] = vm_detail['admin']
        bundle.data['cluster_admin'] = vm_detail['cluster_admin']
        bundle.data['remove'] = vm_detail['remove']
        bundle.data['power'] = vm_detail['power']
        bundle.data['modify'] = vm_detail['modify']
        bundle.data['migrate'] = vm_detail['migrate']
        permissions = {'users':[], 'groups':[]}

        if (vm_detail.has_key('job')):
            bundle.data['job'] = vm_detail['job']
            if (vm_detail['job'] != None):
                bundle.data['job'] = JobResource().get_resource_uri(vm_detail['job'])

        perms = ganeti_web.views.virtual_machine.users(bundle.request, vm.cluster.slug, vm_detail['instance'], rest = True)

        if (perms['users'].__len__() > 0):
            for user in perms['users']:
                permissions['users'].append(UserResource().get_resource_uri(user))

        bundle.data['permissions'] = permissions

        log = ganeti_web.views.virtual_machine.object_log(bundle.request, vm.cluster.slug, vm_detail['instance'], True)
        #obj_res_instances = {'VirtualMachine':VMResource, 'User':UserResource, 'Group':GroupResource, 'Cluster':ClusterResource, 'Node':NodeResource, 'Job':JobResource}
        bundle.data['log'] = api.utils.extract_log_actions(bundle.request, bundle.obj.id, log)

        return bundle

    def obj_get(self, request=None, **kwargs):
        vm = super(VMResource, self).obj_get(request=request, **kwargs)
        vm_detail = ganeti_web.views.virtual_machine.detail(request, vm.cluster.slug, vm.hostname, True)
        return vm_detail['instance'] #TODO CHECK
        #return vm

    def obj_get_list(self, request=None, **kwargs):
        vms = list_(request, True)
        return vms

    def obj_delete(self, request, **kwargs):
        try:
            vm = self.obj_get(request, **kwargs)
        except NotFound:
            raise NotFound("Object not found")
        vm_detail = ganeti_web.views.virtual_machine.detail(request, vm.cluster.slug, vm.hostname, True)
        response = ganeti_web.views.virtual_machine.delete(request, vm.cluster.slug, vm_detail['instance'], True)
        return response

    def post_detail(self, request, **kwargs):

        try:
            deserialized = self.deserialize(request, request.raw_post_data, format=request.META.get('CONTENT_TYPE', 'application/json'))
        except (Exception):
            return HttpBadRequest()
        try:
            vm = self.obj_get(request,id=kwargs.get('pk'))
            #vm = self.obj_get(request,hostname='derpers.gwm.osuosl.org') TODO name manipulations
            vm_detail = ganeti_web.views.virtual_machine.detail(request, vm.cluster.slug, vm.hostname, True)
        except NotFound, Exception:
            return utils.serialize_and_reply(request, "Could not find object", 404)

        deserialized = self.alter_deserialized_detail_data(request, deserialized)

        # action: instance reboot TODO: test rebooting extensively
        if (deserialized.has_key('action')) & (deserialized.get('action')=='reboot'):
            response = ganeti_web.views.virtual_machine.reboot(request, vm.cluster.slug, vm_detail['instance'], True)
            return response

        # action: instance rename
        if (deserialized.has_key('action')) & (deserialized.get('action')=='rename'):

            if ((deserialized.has_key('hostname')) & (deserialized.has_key('ip_check')) & (deserialized.has_key('name_check'))):
                extracted_params = {'hostname':deserialized.get('hostname'), 'ip_check':deserialized.get('ip_check'), 'name_check':deserialized.get('name_check')}
            else:
                return HttpBadRequest
            response = ganeti_web.views.virtual_machine.rename(request, vm.cluster.slug, vm_detail['instance'], True, extracted_params)
            return response

        # action: instance startup
        if (deserialized.has_key('action')) & (deserialized.get('action')=='startup'):
            try:
                response = ganeti_web.views.virtual_machine.startup(request, vm.cluster.slug, vm_detail['instance'], True);
            except Http404:
                return utils.serialize_and_reply(request, "Could not find resource", code=404)
            return utils.serialize_and_reply(request, response['msg'], code=response['code']) #SERIALIZATION

        # action: instance shutdown
        if (deserialized.has_key('action')) & (deserialized.get('action')=='shutdown'):
            try:
                response = ganeti_web.views.virtual_machine.shutdown(request, vm.cluster.slug, vm_detail['instance'], True);
            except Http404:
                return utils.serialize_and_reply(request, "Could not find resource", code=404)
            return utils.serialize_and_reply(request, response['msg'], code=response['code'])

        return HttpAccepted

    def post_list(self, request, **kwargs):
        try:
            deserialized = self.deserialize(request, request.raw_post_data, format=request.META.get('CONTENT_TYPE', 'application/json'))
        except (Exception):
            return HttpBadRequest()
        deserialized = self.alter_deserialized_detail_data(request, deserialized)


        # TODO: move detail and list code in separate place and call it from both detail/list functions
        if (deserialized.has_key('action')):
            if (deserialized.has_key('id')):
                try:
                    vm = self.obj_get(request,id=deserialized.get('id'))
                    vm_detail = ganeti_web.views.virtual_machine.detail(request, vm.cluster.slug, vm.hostname, True)
                except NotFound:
                    raise NotFound("Object not found")
                # reboot instance
                if (deserialized.get('action')=='reboot'):
                    response = ganeti_web.views.virtual_machine.reboot(request, vm.cluster.slug, vm_detail['instance'], True)
                    return response

                # rename instance
                if ((deserialized.has_key('hostname')) & (deserialized.has_key('ip_check')) & (deserialized.has_key('name_check'))):
                    extracted_params = {'hostname':deserialized.get('hostname'), 'ip_check':deserialized.get('ip_check'), 'name_check':deserialized.get('name_check')}
                else:
                    return HttpBadRequest
                response = ganeti_web.views.virtual_machine.rename(request, vm.cluster.slug, vm_detail['instance'], True, extracted_params)
                return response


class JobResource(ModelResource):
    cluster = fields.ForeignKey(ClusterResource, 'cluster', full=False)

    def dehydrate(self, bundle):
        job = bundle.obj
        job_detail = ganeti_web.views.jobs.detail(bundle.request, job.cluster.slug, job.job_id, True)
        if (bundle.obj.info):
            bundle.data['opresult'] = bundle.obj.info['opresult']
            bundle.data['summary'] = bundle.obj.info['summary']
            bundle.data['ops'] = bundle.obj.info['ops']
        bundle.data['cluster_admin'] = job_detail['cluster_admin']
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
