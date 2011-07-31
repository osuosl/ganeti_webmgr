__author__ = 'bojan'

import utils
from tastypie.resources import ModelResource, Resource, HttpAccepted, HttpBadRequest, HttpApplicationError, HttpCreated, HttpResponseNotFound, ResourceOptions
from ganeti_web.models import VirtualMachine, SSHKey, Cluster, Node, CachedClusterObject, Job, ClusterUser
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
        if (vm_detail.has_key('job')):
            bundle.data['job'] = vm_detail['job']
            if (vm_detail['job'] != None):
                bundle.data['job'] = JobResource().get_resource_uri(vm_detail['job'])
        perms = ganeti_web.views.virtual_machine.users(bundle.request, vm.cluster.slug, vm_detail['instance'], rest = True)
        permissions = {'users':[], 'groups':[]}
        if (perms['users'].__len__() > 0):
            for user in perms['users']:
                print (user)
                print UserResource().get_resource_uri(user)
                permissions['users'].append(UserResource().get_resource_uri(user))

        #bundle.data['users']

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

