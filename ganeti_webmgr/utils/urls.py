from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(
    'utils.views',
    url(r'^keys/(?P<api_key>\w+)/$', 'ssh_keys', name="key-list"),
)
