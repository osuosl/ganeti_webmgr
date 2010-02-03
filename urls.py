from django.conf.urls.defaults import *
from django.contrib.auth.views import login, logout

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    #authentication
    (r'^accounts/login/$', login),
    (r'^accounts/logout/$', logout, {'next':'/plugins'}),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    
    (r'^', include('maintain.core.urls')),
)

