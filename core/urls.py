from django.conf.urls.defaults import *

from views import *

urlpatterns = patterns('',
    #default
    (r'^$', plugins),
    (r'^plugin/depends$', depends),
    (r'^plugin/dependeds$', dependeds),
    (r'^plugin/enable$', enable),
    (r'^plugin/disable$', disable),
    (r'^plugin/lock$', refresh_active_lock),
    (r'^plugin/(\w+)/$', config),
    (r'^plugin/(\w+)/save$', config_save)
)


# The following is used to serve up local media files like images, css, js
# Use __file__ to find the absolute path to this file.  This can be used to
# determine the path to the static directory which contains all the files
# we are trying to expose
media_root = '%s/static' % __file__[:__file__.rfind('/')]
baseurlregex = r'^static/(?P<path>.*)$'
urlpatterns += patterns('',
    (baseurlregex, 'django.views.static.serve', {'document_root': media_root})
)