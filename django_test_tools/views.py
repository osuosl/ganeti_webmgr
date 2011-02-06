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

from django.test.client import Client

from django_test_tools.users import UserTestMixin


class ViewTestMixin():
    """
    Helper for testing standard things on a view like anonymous users,
    unauthorized users, and permission tests
    
    this works with predefined users with password=secret and permission defined
    as needed for the specific test.
    """

    def _test_standard_fails(self, url, args, data={}, method='get'):
        """
        tests that a view will react to the following account types:
            * unauthenticated - redirect to login
            * no permissions - 403
            * any invalid args - 404
        
        @param url - url to test
        @param args - args for the url string
        @param data - dictionary of data to be passed to the request
        @param method - http method to be used
        """
        c = Client()
        unauthorized = UserTestMixin.create_user('unauthorized')
        superuser = UserTestMixin.create_user('superuser', is_superuser=True)
        
        # unauthenticated
        response = c.get(url % args, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')
        
        # unauthorized
        self.assert_(c.login(username=unauthorized.username, password='secret'))
        response = c.get(url % args, data)
        self.assertEqual(403, response.status_code)
        
        # test 404s - replace each argument one at a time with a nonexistent value
        self.assert_(c.login(username=superuser.username, password='secret'))
        for i in range(len(args)):
            temp_args = [arg for arg in args]
            temp_args[i] = 'DOES.NOT.EXIST.WILL.FAIL'
            response = c.get(url % tuple(temp_args), data)
            self.assertEqual(404, response.status_code)

    def _test_failed_access(self, url, args, users, data={}, method='get'):
        """
        all users given to this function must fail access
        
        @param url - url to test
        @param args - args for the url string
        @param users - list of users, all of which must result in 403
        @param data - dictionary of data to be passed to the request
        @param method - http method to be used
        """
        c = Client()
        client_method = getattr(c, method)
        
        for user in users:
            self.assert_(c.login(username=user.username, password='secret'))
            response = client_method(url % args, data)
            self.assertEqual(403, response.status_code)

    def _test_successful_access(self, url, args, users, template=None, \
            mime=None, tests=None, setup=False, data={}, method='get',
            follow=False):
        """
        all users given to this function must fail access
        
        @param url - url to test
        @param args - args for the url string
        @param users - list of users, all of which must result in 403
        @param template - if given, template that responses should use
        @param mime - if given, mime for response
        @param tests - a function that executes additional tests
        on the responses from the client
        @param setup - call setup before each iteration
        @param data - dictionary of data to be passed to the request
        @param method - http method to be used
        @param follow - follow http redirect
        """
        mime = mime if mime else 'text/html; charset=utf-8'
        c = Client()
        client_method = getattr(c, method)
        
        for user in users:
            if setup:
                self.setUp()
            
            self.assert_(c.login(username=user.username, password='secret'))
            response = client_method(url % args, data)
            self.assertEqual(200, response.status_code, 'user unauthorized: %s' % user.username )
            self.assertEqual(mime, response['content-type'])
            if template is not None:
                self.assertTemplateUsed(response, template)
            if mime is not None:
                self.assertEqual(response['content-type'], mime)
            
            if tests is not None:
                tests(user, response)