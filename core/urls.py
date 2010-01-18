from django.conf.urls.defaults import *

from views import *

urlpatterns = patterns('',
    #default
    (r'^$', plugins),
    (r'^plugin/depends$', depends),
    (r'^plugin/dependeds$', dependeds),
    (r'^plugin/enable$', enable),
    (r'^plugin/disable$', disable),
    (r'^plugin/(\w+)/$', config),
    (r'^plugin/(\w+)/save$', config_save)
)