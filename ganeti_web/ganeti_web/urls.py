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

from ganeti_web.views.general import AboutView
from ganeti_web.views.vm_template import (TemplateFromVMInstanceView,
                                          VMInstanceFromTemplateView,
                                          TemplateListView)
from virtualmachines.forms import vm_wizard


from clusters.urls import cluster
from virtualmachines.urls import vm_prefix
template = '(?P<template>[^/]+)'
primary_node = 'primary_node/(?P<primary_node>.+)'
secondary_node = 'secondary_node/(?P<secondary_node>.+)'
template_prefix = '%s/template/%s' % (cluster, template)


# general include
urlpatterns = patterns(
    '',
    (r'^', include('object_permissions.urls')),
    (r'^', include('object_log.urls')),
    (r'^', include('muddle_users.urls')),
    (r'^', include('muddle.urls')),

    (r'^', include('auth.urls')),
    (r'^', include('clusters.urls')),
    (r'^', include('jobs.urls')),
    (r'^', include('nodes.urls')),
    (r'^', include('utils.urls')),
    (r'^', include('virtualmachines.urls')),
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

handler500 = 'ganeti_web.views.view_500'


# General
urlpatterns += patterns(
    'ganeti_web.views.general',

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
urlpatterns += patterns(
    'muddle_users.views.user',
    url(r'^accounts/profile/?', 'user_profile', name='profile',
        kwargs={'template': 'ganeti/users/profile.html'}),
)


# VM add wizard
urlpatterns += patterns(
    "ganeti_web.forms.virtual_machine",
    url(r"^vm/add/?$",
    vm_wizard(initial_dict={0: {'choices': [u'hostname']}}),
    name="instance-create"),
)

# VirtualMachineTemplates
urlpatterns += patterns(
    'ganeti_web.views.vm_template',

    url(r'^templates/$', TemplateListView.as_view(), name='template-list'),

    url(r'^template/create/$',
        vm_wizard(initial_dict={0: {'choices': [u'template_name']}}),
        name='template-create'),

    url(r'^%s/?$' % template_prefix, 'detail', name='template-detail'),

    url(r'^%s/delete/?$' % template_prefix, 'delete', name='template-delete'),

    url(r'^%s/edit/?$' % template_prefix, vm_wizard(), name='template-edit'),

    url(r'^%s/copy/?$' % template_prefix, 'copy', name='template-copy'),

    url(r'^%s/vm/?$' % template_prefix, VMInstanceFromTemplateView.as_view(),
        name='instance-create-from-template'),

    url(r'^%s/template/?$' % vm_prefix, TemplateFromVMInstanceView.as_view(),
        name='template-create-from-instance'),
)

# Virtual Machine Importing
urlpatterns += patterns(
    'ganeti_web.views.importing',

    url(r'^import/orphans/', 'orphans',
        name='import-orphans'),
    url(r'^import/missing/', 'missing_ganeti',
        name='import-missing'),
    url(r'^import/missing_db/', 'missing_db',
        name='import-missing_db'),
)

# Node Importing
urlpatterns += patterns(
    'ganeti_web.views.importing_nodes',

    url(r'^import/node/missing/', 'missing_ganeti',
        name='import-nodes-missing'),

    url(r'^import/node/missing_db/', 'missing_db',
        name='import-nodes-missing_db'),
)

# Search
urlpatterns += patterns(
    'ganeti_web.views.search',

    url(r'^search/suggestions.json', 'suggestions', name='search-suggestions'),

    url(r'^search/detail_lookup', 'detail_lookup', name='search-detail-lookup')
)
urlpatterns += patterns(
    'ganeti_web.views.user_search',

    url(r'^search/owners/?$', 'search_owners', name="owner-search")
)
urlpatterns += patterns(
    'haystack.views',
    url(r'^search/',
        login_required(SearchView(form_class=autocomplete_search_form)),
        name='search')
)

# The following is used to serve up local static files like images
root = '%s/static' % os.path.dirname(os.path.realpath(__file__))
urlpatterns += patterns(
    '',
    (r'^static/(?P<path>.*)', 'django.views.static.serve',
     {'document_root': root})
    (r'^favicon.ico', 'django.views.static.serve',
     {'document_root':  settings.STATIC_ROOT, 'path': 'favicon.ico'}),

    # noVNC files
    (r'^novnc/(?P<path>.*)', 'django.views.static.serve',
        {'document_root':  '%s/noVNC/include' % settings.DOC_ROOT}),
)
