from django.conf import settings
from django.conf.urls.defaults import *
from django.contrib.auth.views import login, logout

from views import *


urlpatterns = patterns('',
    
    #default
    (r'^$', plugins),
    
    #plugins
    (r'^plugins$', plugins),
    (r'^plugin/depends$', depends),
    (r'^plugin/dependeds$', dependeds),
    (r'^plugin/enable$', enable),
    (r'^plugin/disable$', disable),
    (r'^plugin/lock/acquire$', acquire_lock),
    (r'^plugin/lock/refresh$', refresh_lock),
    (r'^plugin/(\w+)/$', config),
    (r'^plugin/(\w+)/save$', config_save),
)

# add view managers special view handler only if it is enabled.  By default it
# is a core plugin, but a user could disable it.
if 'ViewManager' in manager:
    urlpatterns += patterns('',
        (r'^o/(?P<path>.+)$', manager['ViewManager'].process),
    )


# The following is used to serve up local media files like images, css, js
# Use __file__ to find the absolute path to this file.  This can be used to
# determine the path to the static directory which contains all the files
# we are trying to expose
media_root = '%s/static' % __file__[:__file__.rfind('/')]
baseurlregex = r'^muddle_static/(?P<path>.*)$'
urlpatterns += patterns('',
    (baseurlregex, 'django.views.static.serve', {'document_root': media_root})
)


# URLS used for testing model glue urls
if settings.DEBUG or True:
    urlpatterns = patterns('muddle.tests.resolvers',
        url(r'^model_resolve_test/(\d+)/(\d+)/$', 'noop_view', name='resolve-test-args'),
        url(r'^model_resolve_test/(?P<one>\d+)/(?P<two>\d+)/$', 'noop_view', name='resolve-test-kwargs'),
    )