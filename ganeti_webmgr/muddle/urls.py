from django.conf import settings
from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('')


# The following is used to serve up local media files like images, css, js
# Use __file__ to find the absolute path to this file.  This can be used to
# determine the path to the static directory which contains all the files
# we are trying to expose
static_root = '%s/static' % __file__[:__file__.rfind('/')]
base_url_regex = r'^muddle_static/(?P<path>.*)$'
urlpatterns += patterns('',
                        (base_url_regex, 'django.views.static.serve',
                         {'document_root': static_root})
                        )
