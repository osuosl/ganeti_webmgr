from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('muddle.settings.views',
    url(r'^/?$', 'index', name='muddle-settings'),
    url(r'^(?P<category>\w+)/?$', 'detail', name='muddle-settings-category'),
    url(r'^(?P<category>\w+)/(?P<subcategory>\w+)?$', 'save', name='muddle-settings-save'),

)