# Copyright (C) 2010 Oregon State University et al.
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
from django.conf.urls.defaults import patterns, url

# If muddled.shots is installed then load templates that allow mixers to extend
# the templates.  Otherwise use standard templates.  The standard templates can
# still be overridden by manually adding a url with a different template
# attribute
if 'muddle.shots' in settings.INSTALLED_APPS:
    USER_TEMPLATE = 'muddle/user/detail.html'
    GROUP_TEMPLATE = 'muddle/group/detail.html'
    GROUP_LIST_TEMPLATE = 'muddle/group/list.html'
    USER_ROW_TEMPLATE = 'muddle/group/user_row.html'
else:
    USER_TEMPLATE = 'user/detail.html'
    GROUP_TEMPLATE = 'group/detail.html'
    GROUP_LIST_TEMPLATE = 'group/list.html'
    USER_ROW_TEMPLATE = 'group/user_row.html'


# Users
urlpatterns = patterns(
    'ganeti_webmgr.muddle_users.views.user',
    url(r'^accounts/profile/?', 'user_profile', name="profile"),
    url(r'^users/?$', 'user_list', name="user-list"),
    url(r'^user/add/?$', 'user_add', name="user-create"),
    url(r'^user/(?P<user_id>\d+)/?$', 'user_detail',
        {'template': USER_TEMPLATE}, name="user-detail"),
    url(r'^users/(?P<username>[\w@.+-]+)/?$', 'user_detail',
        {'template': USER_TEMPLATE}, name="user-detail-name"),
    url(r'^user/(?P<user_id>\d+)/edit/?$', 'user_edit', name="user-edit"),
    url(r'^user/(?P<user_id>\d+)/password/?$', 'user_password', name="user-password"),
)

# Groups
urlpatterns += patterns(
    'ganeti_webmgr.muddle_users.views.group',
    # Groups
    url(r'^groups/$', 'list', {'template': GROUP_LIST_TEMPLATE}, name="group-list"),
    url(r'^group/add/?$', 'edit', name="group-add"),
    url(r'^group/(?P<id>\d+)/?$', 'detail', {'template': GROUP_TEMPLATE},
        name="group-detail"),
    url(r'^group/(?P<id>\d+)/edit/?$', 'edit', name="group-edit"),
    url(r'^group/(?P<id>\d+)/user/add/?$', 'add_user',
        {'user_row_template': USER_ROW_TEMPLATE}, name="group-add-user"),
    url(r'^group/(?P<id>\d+)/user/remove/?$', 'remove_user',
        name="group-remove-user"),
)
