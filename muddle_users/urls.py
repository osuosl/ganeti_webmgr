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

from django.conf.urls.defaults import patterns, url

# Users
urlpatterns = patterns('muddle_users.views.user',
    url(r'^accounts/profile/?', 'user_profile', name="profile"),
    url(r'^users/?$', 'user_list', name="user-list"),
    url(r'^user/add$', 'user_add', name="user-create"),
    url(r'^user/(?P<user_id>\d+)/?$', 'user_detail', name="user-detail"),
    url(r'^user/(?P<user_id>\d+)/edit/?$', 'user_edit', name="user-edit"),
    url(r'^user/(?P<user_id>\d+)/password/?$', 'user_password', name="user-password"),
)

# Groups
urlpatterns += patterns('muddle_users.views.group',
    # Groups
    url(r'^groups/$', 'list', name="usergroup-list"),
    url(r'^group/?$', 'detail', name="usergroup"),
    url(r'^group/(?P<id>\d+)/?$', 'detail', name="usergroup-detail"),
    url(r'^group/(?P<id>\d+)/user/add/?$','add_user', name="usergroup-add-user"),
    url(r'^group/(?P<id>\d+)/user/remove/?$','remove_user', name="usergroup-remove-user"),
)