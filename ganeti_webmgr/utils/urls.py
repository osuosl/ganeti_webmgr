from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(
    'ganeti_webmgr.utils.views',
    url(r'^keys/(?P<api_key>[^/]+)/$', 'ssh_keys', name="key-list"),
)
