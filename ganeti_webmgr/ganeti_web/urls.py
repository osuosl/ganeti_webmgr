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
import os

from forms.autocomplete_search_form import autocomplete_search_form
from haystack.views import SearchView

from django.conf import settings
from django.conf.urls.defaults import patterns, url, include
from django.contrib.auth.decorators import login_required

from ganeti_webmgr.ganeti_web.views.general import AboutView
from ganeti_webmgr.virtualmachines.forms import vm_wizard


handler500 = 'ganeti_webmgr.ganeti_web.views.view_500'


# TODO: is this used anywhere?  Probably not.  Get rid of it.
primary_node = 'primary_node/(?P<primary_node>.+)'
secondary_node = 'secondary_node/(?P<secondary_node>.+)'


# general include
urlpatterns = patterns(
    '',
    (r'^', include('object_permissions.urls')),
    (r'^', include('object_log.urls')),

    (r'^', include('ganeti_webmgr.authentication.urls')),
    (r'^', include('ganeti_webmgr.clusters.urls')),
    (r'^', include('ganeti_webmgr.jobs.urls')),
    (r'^', include('ganeti_webmgr.nodes.urls')),
    (r'^', include('ganeti_webmgr.utils.urls')),
    (r'^', include('ganeti_webmgr.virtualmachines.urls')),
    (r'^', include('ganeti_webmgr.vm_templates.urls')),
    (r'', include('ganeti_webmgr.ganetiviz.urls')),
)

# user management and authentication
urlpatterns += patterns(
    '',
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
urlpatterns += patterns('', (r'^i18n/', include('django.conf.urls.i18n')))


# General
urlpatterns += patterns(
    'ganeti_webmgr.ganeti_web.views.general',

    url(r'^$', 'overview', name="index"),

    # Status page
    url(r'^overview/?$', 'overview', name="overview"),
    url(r'^used_resources/?$', 'used_resources', name="used_resources"),

    url(r'^error/clear/(?P<pk>\d+)/?$', 'clear_ganeti_error',
        name="error-clear"),

    url(r'clusters/errors', 'get_errors', name="cluster-errors"),

    url(r'^about/?$', AboutView.as_view(), name="about"),
)


# Users - overridden from users app to use custom templates
# TODO: IT DOES NOT OVERRIDE
urlpatterns += patterns(
    'ganeti_webmgr.muddle_users.views.user',
    url(r'^accounts/profile/?', 'user_profile', name='profile',
        kwargs={'template': 'ganeti/users/profile.html'}),
)


# VM add wizard
urlpatterns += patterns(
    "ganeti_webmgr.ganeti_web.forms.virtual_machine",
    url(r"^vm/add/?$",
        vm_wizard(initial_dict={0: {'choices': [u'hostname']}}),
        name="instance-create"),
)


# Virtual Machine Importing
urlpatterns += patterns(
    'ganeti_webmgr.ganeti_web.views.importing',

    url(r'^import/orphans/', 'orphans',
        name='import-orphans'),
    url(r'^import/missing/', 'missing_ganeti',
        name='import-missing'),
    url(r'^import/missing_db/', 'missing_db',
        name='import-missing_db'),
)


# Node Importing
urlpatterns += patterns(
    'ganeti_webmgr.ganeti_web.views.importing_nodes',

    url(r'^import/node/missing/', 'missing_ganeti',
        name='import-nodes-missing'),

    url(r'^import/node/missing_db/', 'missing_db',
        name='import-nodes-missing_db'),
)


# Search
urlpatterns += patterns(
    'ganeti_webmgr.ganeti_web.views.search',

    url(r'^search/suggestions.json', 'suggestions', name='search-suggestions'),

    url(r'^search/detail_lookup', 'detail_lookup', name='search-detail-lookup')
)

urlpatterns += patterns(
    'ganeti_webmgr.ganeti_web.views.user_search',

    url(r'^search/owners/?$', 'search_owners', name="owner-search")
)
urlpatterns += patterns(
    'haystack.views',
    url(r'^search/',
        login_required(SearchView(form_class=autocomplete_search_form)),
        name='search')
)


# Moved here so that our overriding works
urlpatterns += patterns(
    '',
    (r'^', include('ganeti_webmgr.muddle_users.urls')),
    (r'^', include('ganeti_webmgr.muddle.urls')),
)
