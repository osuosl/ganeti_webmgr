# Copyright (C) 2010 Oregon State University et al.
# Copyright (C) 2010 Greek Research and Technology Network
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.


from django.conf import settings
from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
#from django.contrib import admin
#admin.autodiscover()

urlpatterns = patterns(
    '',
    (r'^', include('ganeti_web.urls')),
    (r'^', include('object_permissions.urls')),
    (r'^', include('object_log.urls')),
    (r'^', include('muddle_users.urls')),
    (r'^', include('muddle.urls')),

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
    url(r'^accounts/login/?', 'django.contrib.auth.views.login',
        name="login",),
    url(r'^accounts/logout/?', 'django.contrib.auth.views.logout',
        {'next_page': '/'}, name="logout"),
    (r'^accounts/', include('registration.urls')),

    # Explicit 500 test route
    (r'^500/$', 'django.views.generic.simple.direct_to_template',
     {'template': "500.html"})
)
# Language settings
urlpatterns += patterns('',
                        (r'^i18n/', include('django.conf.urls.i18n')),
                        )
handler500 = 'ganeti_web.views.view_500'


#The following is used to serve up local static files like images
urlpatterns += patterns(
    '',
    (r'^favicon.ico', 'django.views.static.serve',
    {'document_root':  settings.STATIC_ROOT,
     'path': 'favicon.ico'}),

    # noVNC files
    (r'^novnc/(?P<path>.*)', 'django.views.static.serve',
        {'document_root':  '%s/noVNC/include' % settings.DOC_ROOT}),
)
