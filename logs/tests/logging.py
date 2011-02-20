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

from datetime import datetime
from django.test.client import Client

from django.contrib.auth.models import User, Group
from django.test import TestCase

from ganeti.models import Profile
from logs.models import LogItem, LogAction, register_defaults


class TestLogActionModel(TestCase):

    def setUp(self):
        self.tearDown()

    def tearDown(self):
        #LogAction.objects.all().delete()
        register_defaults()

    def test_trivial(self):
        LogAction()
    
    def test_log_action_register(self):
        """
        tests registering a log action
        """
        LogAction.objects.register('testing', 'test/template.html')
        action = LogAction.objects.get(name='testing')
        self.assertEqual(action.template, 'test/template.html')

    def test_log_action_multiple_register(self):
        """
        Tests re-registering a log action:

        verifies that template can be changed.
        """
        LogAction.objects.register('testing', 'test/template.html')
        LogAction.objects.register('testing', 'test/new/template.html')
        action = LogAction.objects.get(name='testing')
        self.assertEqual(action.template, 'test/new/template.html')

    def test_get_from_cache(self):
        """
        Tests retrieving cached template
        """
        LogAction.objects.register('testing', 'test/template.html')

        # test that object is loaded
        action = LogAction.objects.get_from_cache('testing')
        self.assertTrue(action is not None)

        # test that object is cached
        cached_action = LogAction.objects.get_from_cache('testing')
        self.assertTrue(cached_action is not None)
        self.assertEquals(id(action), id(cached_action))

        # test that re-register updates cache
        LogAction.objects.register('testing', 'test/new/template.html')
        cached_action = LogAction.objects.get_from_cache('testing')
        self.assertEquals(id(action), id(cached_action))
        self.assertEqual(action.template, 'test/new/template.html')


class TestLogItemModel(TestCase):
    def setUp(self):
        self.tearDown()

        user1 = User(username="Mod")
        user1.save()
        
        user2 = User(username="Joe User")
        user2.save()

        dict_ = globals()
        dict_["user1"] = user1
        
        #dict_ = globals()
        dict_["user2"] = user2

        print '??????? registed?'
        register_defaults()

    def tearDown(self):
        User.objects.all().delete()
        Profile.objects.all().delete()
        LogItem.objects.all().delete()
        LogItem.objects.clear_cache()

    def test_log_creation(self):
        """
        Test different ways of creation of LogItem, LogAction

        Verifies:
            * LogItem, LogAction are created/deleted properly
        """
        
        self.assertEqual(len(LogItem.objects.all()), 0)
        self.assertEqual(len(LogAction.objects.all()), 3)
                
        log_item = LogItem.objects.log_action("EDIT", user1, user2,)
        self.assertTrue(log_item is not None)
        LogItem.objects.log_action("DELETE", user1, user2,)
        self.assertEqual(len(LogItem.objects.all()), 2)
        
        LogItem.objects.log_action("EDIT", user1, user2,)
        self.assertEqual(len(LogItem.objects.all()), 3)


    def test_log_representation(self):
        """
        Test representation of LogItems

        Verifies:
            * LogItem is represented properly
        """

        item1 = LogItem.objects.log_action('EDIT', user1, user2,)
        item2 = LogItem.objects.log_action('DELETE', user1, user2,)

        # XXX manually set timestamp so we can check the output consistently
        timestamp = datetime.fromtimestamp(1285799513.4741000)
        item1.timestamp = timestamp
        item2.timestamp = timestamp

        self.assertEqual('<td class="timestamp">29/09/2010 15:31</td><td>Mod edited user Joe User</td>', str(item1))
        self.assertEqual('<td class="timestamp">29/09/2010 15:31</td><td>Mod deleted user Joe User</td>', str(item2))


class TestObjectLogViews(TestCase):

    def setUp(self):
        self.tearDown()

        register_defaults()

        superuser = User(username='superuser', is_superuser=True)
        unauthorized = User(username='unauthorized')
        superuser.set_password('secret')
        unauthorized.set_password('secret')
        superuser.save()
        unauthorized.save()
        self.superuser = superuser
        self.unauthorized = unauthorized

        group = Group.objects.create(name='test')
        self.group = group

        # create some sample logitems
        # superuser editing user
        log = LogItem.objects.log_action
        log('CREATE', superuser, unauthorized)
        log('EDIT', superuser, unauthorized)
        log('DELETE', superuser, unauthorized)
        log('EDIT', superuser, unauthorized)

        # logitems with user in additional fields
        log('EDIT', superuser, superuser, unauthorized)
        log('EDIT', superuser, superuser, superuser, unauthorized)

        # user editing self
        log('EDIT', unauthorized, unauthorized)
        log('EDIT', unauthorized, unauthorized)



    def tearDown(self):
        User.objects.all().delete()
        Group.objects.all().delete()
        LogItem.objects.all().delete()


    def test_list_for_user(self):
        """ tests list_for_user and list_for_object """

        c = Client()
        superuser = self.superuser
        unauthorized = self.unauthorized
        url = '/user/%s/object_log/'
        args = (unauthorized.pk, )

        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assert_(c.login(username=unauthorized.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)

        # superuser - unknown user
        self.assert_(c.login(username=superuser.username, password='secret'))
        response = c.get(url % -1)
        self.assertEqual(404, response.status_code)

        # superuser - checking self
        response = c.get(url % superuser.pk )
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, response.context['log'].count(), response.content)

        # superuser - checking other user
        response = c.get(url % args )
        self.assertEqual(200, response.status_code)
        self.assertEqual(8, response.context['log'].count())

    def test_list_user_actions(self):
        """ tests list_for_user and list_for_object """
        c = Client()
        superuser = self.superuser
        unauthorized = self.unauthorized
        url = '/user/%s/actions'
        args = (unauthorized.pk, )

        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assert_(c.login(username=unauthorized.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)

        # superuser - unknown user
        self.assert_(c.login(username=superuser.username, password='secret'))
        response = c.get(url % -1)
        self.assertEqual(404, response.status_code)

        # superuser - checking self
        response = c.get(url % superuser.pk )
        self.assertEqual(200, response.status_code)
        self.assertEqual(6, response.context['log'].count())

        # superuser - checking other user
        response = c.get(url % args )
        self.assertEqual(200, response.status_code)
        self.assertEqual(2, response.context['log'].count())

    def test_list_group_actions(self):
        """ tests list_for_group """
        c = Client()
        superuser = self.superuser
        unauthorized = self.unauthorized
        url = '/group/%s/object_log'
        args = (self.group.pk, )

        LogItem.objects.log_action('EDIT', superuser, self.group)

        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assert_(c.login(username=unauthorized.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)

        # superuser - unknown user
        self.assert_(c.login(username=superuser.username, password='secret'))
        response = c.get(url % -1)
        self.assertEqual(404, response.status_code)

        # superuser - checking self
        response = c.get(url % args )
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, response.context['log'].count())