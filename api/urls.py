from ganeti_web.models import log_action

__author__ = 'bojan'

from django.contrib.auth.models import User
from django.conf.urls.defaults import *
from api.resources import SSHKeyResource, NodeResource, GroupResource, VMResource, ClusterResource, UserResource, JobResource
from tastypie.api import Api
from tastypie.models import ApiKey

def create_api_keys():
      """Goes through all users and adds API keys for any that don't have one."""
      for user in User.objects.all().iterator():

          try:
              api_key = ApiKey.objects.get(user=user)

              if not api_key.key:
                  # Autogenerate the key.
                  api_key.save()

          except ApiKey.DoesNotExist:
              api_key = ApiKey.objects.create(user=user)



v1_api = Api(api_name='api')
v1_api.register(UserResource())
v1_api.register(VMResource())
v1_api.register(SSHKeyResource())
v1_api.register(ClusterResource())
v1_api.register(NodeResource())
v1_api.register(JobResource())
#v1_api.register(ClusterUserResource())
v1_api.register(GroupResource())

# the keys for new users will be automatically generated on first start
create_api_keys()

urlpatterns = patterns('',
    (r'^', include(v1_api.urls)),
    #(r'^/aapi/', include(v1_api.urls)),
#    (r'^/api/', include(user_resource.urls)),
 #   (r'^/api/', include(vm_resource.urls)),
)
