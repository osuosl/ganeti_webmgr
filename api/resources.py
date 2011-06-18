
__author__ = 'bojan'

from tastypie.resources import ModelResource, Resource, HttpAccepted, HttpBadRequest, HttpApplicationError, HttpCreated
from django.contrib.auth.models import User
from ganeti_web.models import VirtualMachine, SSHKey
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
    user=fields.IntegerField('user_id')
    class Meta:
        queryset = SSHKey.objects.all()
        resource_name = 'ssh_key'
        allowed_methods = ['get']
        authentication = BasicAuthentication()
        authorization = SuperuserAuthorization()


#User.user_permissions.
class VMResource(ModelResource):
    class Meta:
        queryset = VirtualMachine.objects.all()
        resource_name = 'vm'
        allowed_methods = ['get']




