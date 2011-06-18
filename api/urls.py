__author__ = 'bojan'


from django.conf import settings
from django.conf.urls.defaults import *
from api.resources import UserResource, VMResource, SSHKeyResource
from tastypie.api import Api

v1_api = Api(api_name='api')
v1_api.register(UserResource())
v1_api.register(VMResource())
v1_api.register(SSHKeyResource())

urlpatterns = patterns('',
    (r'^', include(v1_api.urls)),
    #(r'^/aapi/', include(v1_api.urls)),
#    (r'^/api/', include(user_resource.urls)),
 #   (r'^/api/', include(vm_resource.urls)),
)
