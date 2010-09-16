from django.conf.urls.defaults import *
from django.views.generic.list_detail import object_list, object_detail
from ganeti_webmgr.ganeti.models import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    # (r'^ganeti_webmgr/', include('ganeti_webmgr.foo.urls')),
    (r'^/?$', object_list, {
        'queryset': Cluster.objects.all(),
        'paginate_by': 15, 
        'template_name': 'index.html', },
        'cluster_overview',
    ),

    (r'^cluster/(?P<slug>\w+)/?$', object_detail, {
        'queryset': Cluster.objects.all(),
        'template_name': 'cluster.html',
        }, 'cluster_detail'),

    url(r'^cluster/(?P<cluster_slug>\w+)/(?P<instance>[^/]+)/vnc/?$',
        'ganeti_webmgr.ganeti.views.vnc', name="instance-vnc"),
    url(r'^cluster/(?P<cluster_slug>\w+)/(?P<instance>[^/]+)/shutdown/?$',
        'ganeti_webmgr.ganeti.views.shutdown', name="instance-shutdown"),
    url(r'^cluster/(?P<cluster_slug>\w+)/(?P<instance>[^/]+)/startup/?$',
        'ganeti_webmgr.ganeti.views.startup', name="instance-startup"),
    url(r'^cluster/(?P<cluster_slug>\w+)/(?P<instance>[^/]+)/reboot/?$',
        'ganeti_webmgr.ganeti.views.reboot', name="instance-reboot"),
    url(r'^cluster/(?P<cluster_slug>\w+)/(?P<instance>[^/]+)/?',
        'ganeti_webmgr.ganeti.views.instance', name="instance-detail"),
    url(r'^user/login/?', 'ganeti_webmgr.ganeti.views.login_view', name="login"),
    url(r'^user/logout/?', 'ganeti_webmgr.ganeti.views.logout_view', name="logout"),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/(.*)', admin.site.root),
)
