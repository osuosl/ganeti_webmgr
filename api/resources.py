
__author__ = 'bojan'

from tastypie.resources import ModelResource, Resource, HttpAccepted, HttpBadRequest, HttpApplicationError, HttpCreated, HttpResponseNotFound
from django.contrib.auth.models import User
from ganeti_web.models import VirtualMachine, SSHKey, Cluster, Node, CachedClusterObject
from tastypie import fields
from tastypie.authentication import Authentication, BasicAuthentication
from tastypie.authorization import Authorization, DjangoAuthorization
from tastypie.bundle import Bundle
from tastypie.exceptions import NotFound
from authorization import SuperuserAuthorization
from django.http import HttpRequest
import ganeti_web.views.users
from django import forms
from tastypie.validation import Validation, FormValidation
from django.contrib.auth.forms import UserCreationForm
from tastypie.utils.dict import dict_strip_unicode_keys
from api.validation import UserValidation
from ganeti_web.views.general import overview
from django.core.context_processors import request
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from tastypie.http import HttpMultipleChoices
from ganeti_web.views.cluster import list_, detail

class UserResource(ModelResource):
    """
    Defines user resource, providing ssh_keys additionally
    """
    class Meta:
        queryset = User.objects.all()
        resource_name = 'user'
        allowed_methods = ['get', 'put', 'post', 'delete']
        authentication = BasicAuthentication()
        authorization = SuperuserAuthorization()
        validation = UserValidation()


    def dehydrate(self, bundle):
        ssh_keys = []
        for key in SSHKey.objects.filter(user__pk=bundle.obj.id):
            ssh_keys.append(key.key)
        bundle.data['ssh_keys'] = ssh_keys
        return bundle

    def put_detail(self, request, **kwargs):
        try:
            deserialized = self.deserialize(request, request.raw_post_data, format=request.META.get('CONTENT_TYPE', 'application/json'))
        except (Exception):
            return HttpBadRequest()
        deserialized = self.alter_deserialized_detail_data(request, deserialized)
        bundle = self.build_bundle(data=dict_strip_unicode_keys(deserialized))
        self.is_valid(bundle, request)
        updated_bundle = self.obj_update(bundle, request=request, pk=kwargs.get('pk'))
        return HttpAccepted



class SSHKeyResource(ModelResource):
    """
    Defines ssh key resource, providing user_id additionally
    """
    user = fields.IntegerField('user_id')
    class Meta:
        queryset = SSHKey.objects.all()
        resource_name = 'ssh_key'
        allowed_methods = ['get']
        authentication = BasicAuthentication()
        authorization = SuperuserAuthorization()


class CachedCluster(ModelResource):
    class Meta:
        object_class = CachedClusterObject
        #queryset = CachedClusterObject.objects.all()
        resource_name='cco'
        

class VMResource(ModelResource):
    class Meta:
        queryset = VirtualMachine.objects.all()
        resource_name = 'vm'
        allowed_methods = ['get']
        fields = {'id', 'ram','disk_size','hostname','cluster_id','operating_system', 'virtual_cpus'}


class ClusterResource(ModelResource):
    class Meta:
        resource_name = 'cluster'
        object_class = Cluster
        allowed_methods=['get']
        queryset = Cluster.objects.all()
        fields = ['username','id', 'disk', 'description','hostname', 'ram','slug','port','virtual_cpus']

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
        #bundle.data['info'] = detail(request, bundle.obj.slug, True)['cluster']
        bundle.data['info']=bundle.obj.info
        bundle.data['quota'] = bundle.obj.get_quota(user=User.objects.get(username=request.META['USER']).id if (request.META.has_key("USER")) else None)
        bundle.data['default_quota'] = bundle.obj.get_default_quota()
        print bundle.obj.info
        return self.create_response(request, bundle)
        

    def get_object_list(self, request):
        objects = Cluster.objects.all()
        return objects
        
        
    def obj_get_list(self, request=None, **kwargs):
        return self.get_object_list(request)