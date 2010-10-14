from django.conf import settings
from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    (r'^', include('ganeti.urls')),
    (r'^', include('object_permissions.urls')),
    

    # user management
    # account/activate/<key>/ - Activate a user
    # account/activate/complete/ - Ater-activation page
    # account/register/ - User registration form
    # account/register/complete/ - After-registration page
    # account/register/closed/ - No registration allowed page
    # ---
    # account/login - login page
    # account/logout - logout page
    # account/password/reset/ - send password reset email
    # account/password/change/ - change current user password
    
    # Authentication
    url(r'^accounts/login/?', 'django.contrib.auth.views.login',  name="login",),
    url(r'^accounts/logout/?', 'django.contrib.auth.views.logout', \
                        {'next_page':'/'}, name="logout"),
    (r'^accounts/', include('registration.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    
    (r'^500/$', 'django.views.generic.simple.direct_to_template', {'template':"500.html"})
)



#The following is used to serve up local media files like images
#if settings.LOCAL_DEV:
if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)', 'django.views.static.serve',\
         {'document_root':  settings.MEDIA_ROOT}),
    )
    