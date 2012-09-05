from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('muddle.settings.views',
    url(r'^settings/?$', 'index', name='muddle-settings'),
    url(r'^settings/(?P<category>\w+)/?$', 'detail', name='muddle-settings-category'),
    url(r'^settings/(?P<category>\w+)/(?P<subcategory>\w+)?$', 'save', name='muddle-settings-save'),
)