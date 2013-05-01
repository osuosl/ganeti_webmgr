# Copyright (C) 2011 Oregon State University et al.
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

from django.contrib.auth.models import User


class UserTestMixin():
    """
    Mixin providing functions for easily creating users
    """

    @classmethod
    def create_user(cls, username='tester', **kwargs):
        user, new = User.objects.get_or_create(username=username, **kwargs)
        user.set_password('secret')
        user.save()
        return user

    def create_users(self, users, context=None):
        """
        Given a list of user names, create each user.

        The users will be placed into a dict which will be returned. To use an
        existing dict, override the ``context`` parameter.

        The users will also be added to this class under their given names.

        @param users - list of user names
        @param context - dictionary to add users too
        @return a dictionary of the users.
        """

        if context is None:
            context = {}

        for name in users:
            name, kwargs = name if isinstance(name, (tuple,)) else (name, {})
            user = self.create_user(name, **kwargs)
            # New behavior: Add the user directly to this class.
            setattr(self, name, user)
            context.update({name: user})

        return context

    def create_standard_users(self, context=None):
        """
        Create two common users: "unauthorized", a user who is not authorized
        to do things, and "superuser", a superuser.
        """

        if context is None:
            context = {}

        return self.create_users([
            'unauthorized',
            ('superuser',{'is_superuser':True})
        ], context)
