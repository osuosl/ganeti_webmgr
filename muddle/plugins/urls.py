from django.conf.urls.defaults import patterns

urlpatterns = patterns('muddle.plugins.views',

    #default
    (r'^$', 'plugins'),

    #plugins
    (r'^plugins$', 'plugins'),
    (r'^plugin/depends$', 'depends'),
    (r'^plugin/dependeds$', 'dependeds'),
    (r'^plugin/enable$', 'enable'),
    (r'^plugin/disable$', 'disable'),
    (r'^plugin/lock/acquire$', 'acquire_lock'),
    (r'^plugin/lock/refresh$', 'refresh_lock'),
    (r'^plugin/(\w+)/$', 'config'),
    (r'^plugin/(\w+)/save$', 'config_save'),
)