from django.conf.urls.defaults import *

from views import *

urlpatterns = patterns('',
    #default
    (r'^$', plugins)
)