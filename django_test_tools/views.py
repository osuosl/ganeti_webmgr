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

    def assert_404(self, url, args, data=dict(), method='get'):
        """
        Verifies that invalid url args will result in 404

        @param url - url to test
        @param args - args for the url string
        @param data - dictionary of data to be passed to the request
        @param method - http method to be used
        """
        c = Client()
        superuser = UserTestMixin.create_user('superuser', is_superuser=True)
        method = getattr(c, method)

        # test 404s - replace each argument one at a time with a nonexistent value
        self.assertTrue(c.login(username=superuser.username, password='secret'))
        for i in range(len(args)):
            temp_args = [arg for arg in args]
            temp_args[i] = 'DOES.NOT.EXIST.WILL.FAIL'
            response = method(url % tuple(temp_args), data)
            self.assertEqual(404, response.status_code)

    def assert_401(self, url, args, data=dict(), method='get'):
        """
        Asserts that an anonymous user will be required to login

        @param url - url to test
        @param args - args for the url string
        @param data - dictionary of data to be passed to the request
        @param method - http method to be used
        """
        c = Client()
        method = getattr(c, method)
        response = method(url % args, data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

    def assert_standard_fails(self, url, args, data=dict(), method='get', login_required=True, authorized=True):
        """
        shortcut function for running standard tests:
            * assert_404
            * assert_401 for anonymous user
            * assert_403 for a user with no permissions
        
        @param url - url to test
        @param args - args for the url string
        @param data - dictionary of data to be passed to the request
        @param method - http method to be used
        @param login_required - run assert_401 test, default=True
        @param authorized - run assert_403 test for unauthorized user, default=True
        """
        # unauthenticated
        if login_required:
            self.assert_401(url, args, data, method)
        
        # unauthorized
        if authorized:
            unauthorized = UserTestMixin.create_user('unauthorized')
            self.assert_403(url, args, [unauthorized], data, method)

        # test 404s - replace each argument one at a time with a nonexistent value
        self.assert_404(url, args)

    def assert_403(self, url, args, users, data=dict(), method='get'):
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
            self.assertTrue(c.login(username=user.username, password='secret'))
            response = client_method(url % args, data)
            self.assertEqual(403, response.status_code)

    def assert_200(self, url, args, users, template=None, \
            mime=None, tests=None, setup=False, data=dict(), method='get',
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
            
            self.assertTrue(c.login(username=user.username, password='secret'))
            response = client_method(url % args, data, follow=follow)
            self.assertEqual(200, response.status_code, 'user unauthorized: %s' % user.username )
            if template is not None:
                self.assertTemplateUsed(response, template)
            if mime is not None:
                self.assertEqual(response['content-type'], mime)
            
            if tests is not None:
                tests(user, response)

    def assert_view_missing_fields(self, url, args, data, fields=None, \
                   template=None, mime=None, tests=None, method='post'):
        """
        Tests fields that should raise an error in a view, usually from form
        validation

        @param url - url to test
        @param args - args for the url string
        @param data - dictionary of data to be passed to the request
        @param fields - list of field keys that are required
        @param template - if given, template that responses should use
        @param mime - if given, mime for response
        @param tests - a function that executes additional tests
        on the responses from the client
        @param method - http method to be used
        """
        fields = data.keys if fields is None else fields
        mime = mime if mime else 'text/html; charset=utf-8'
        c = Client()
        client_method = getattr(c, method)
        superuser = UserTestMixin.create_user('superuser', is_superuser=True)

        self.assertTrue(c.login(username=superuser.username, password='secret'))

        # check required fields
        for name in fields:
            data_ = data.copy()
            del data_[name]

            response = client_method(url%args, data_)
            self.assertEqual(200, response.status_code )
            if template is not None:
                self.assertTemplateUsed(response, template)
            if mime is not None:
                self.assertEqual(response['content-type'], mime)
            if tests is not None:
                tests(superuser, response)

    def assert_view_values(self, url, args, data, fields, \
                   template=None, mime=None, tests=None, method='post'):
        """
        Tests fields that should raise an error for a specific type of invalid
        data is sent.  This is used for blackbox testing form validation via
        the view it is used in.

        @param url - url to test
        @param args - args for the url string
        @param data - dictionary of data to be passed to the request
        @param fields - list of dictionaries of invalid data combinations
        @param template - if given, template that responses should use
        @param mime - if given, mime for response
        @param tests - a function that executes additional tests
        on the responses from the client
        @param method - http method to be used
        """
        mime = mime if mime else 'text/html; charset=utf-8'
        c = Client()
        client_method = getattr(c, method)
        superuser = UserTestMixin.create_user('superuser', is_superuser=True)

        self.assertTrue(c.login(username=superuser.username, password='secret'))

        # check required fields
        for values in fields:
            data_ = data.copy()
            data_.update(values)
            response = client_method(url%args, data_)
            self.assertEqual(200, response.status_code )
            if template is not None:
                self.assertTemplateUsed(response, template)
            if mime is not None:
                self.assertEqual(response['content-type'], mime)
            if tests is not None:
                tests(superuser, response)