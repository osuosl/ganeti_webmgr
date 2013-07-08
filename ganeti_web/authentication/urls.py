from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(
    'authentication.views',

    url(r'^user/(?P<user_id>\d+)/key/?$',
        'key_get',
        name="user-key-add"),

    url(r'^keys/get/$', 'key_get', name="key-get"),
    url(r'^keys/get/(?P<key_id>\d+)/?$', 'key_get', name="key-get"),
    url(r'^keys/save/$', 'key_save', name="key-save"),
    url(r'^keys/save/(?P<key_id>\d+)/?$', 'key_save', name="key-save"),
    url(r'^keys/delete/(?P<key_id>\d+)/?$', 'key_delete', name="key-delete"),
)
