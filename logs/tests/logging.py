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


from django.contrib.auth.models import User
from django.test import TestCase
from django.contrib.contenttypes.models import ContentType
from django.utils.encoding import force_unicode

from django.conf import settings
from django import db

from ganeti.models import Profile
from logs.models import LogItem, LogAction


class LoggingTest(TestCase):
    def setUp(self):
        self.tearDown()

        user = User(username="testing")
        user.save()
        profile = user.get_profile()

        act1 = LogAction(name="creation", action_message="created")
        act1.save()

        dict_ = globals()
        dict_["act1"] = act1
        dict_["user"] = user
        dict_["profile"] = profile

    def tearDown(self):
        Profile.objects.all().delete()
        LogItem.objects.all().delete()
        LogAction.objects.all().delete()
        LogItem.objects.clear_cache()

    def test_log_creation(self):
        """
        Test different ways of creation of LogItem, LogAction

        Verifies:
            * LogItem, LogAction are created/deleted properly
        """
        self.assertTrue(LogAction.objects.filter(pk=act1.pk).exists())

        pk1 = LogItem.objects.log_action(
            user = profile,
            affected_object = user,
            action = act1,
            log_message = "started test #1",
        )
        pk2 = LogItem.objects.log_action(
            user = profile,
            affected_object = user,
            action = "delete",
            #log_message = "stopped test #1",
        )

        self.assertEqual(len(LogItem.objects.all()), 2)
        self.assertEqual(len(LogAction.objects.all()), 2)

    def test_log_representation(self):
        """
        Test representation of LogItems

        Verifies:
            * LogItem is represented properly
        """
        pk1 = LogItem.objects.log_action(
            user = profile,
            affected_object = user,
            action = act1,
            log_message = "started test #1",
        )
        pk2 = LogItem.objects.log_action(
            user = profile,
            affected_object = user,
            action = "delete",
            #log_message = "stopped test #1",
        )
        item1 = LogItem.objects.get( pk=pk1 )
        item2 = LogItem.objects.get( pk=pk2 )

        self.assertEqual(repr(item1),
            "[%s] user testing created user \"testing\": started test #1" % item1.timestamp,
        )
        self.assertEqual(repr(item2),
            "[%s] user testing deleteed user \"testing\"" % item2.timestamp,
        )

    def test_caching(self):
        """
        Test LogAction caching. Test based on ContentType doctest.

        Verifies:
            * LogAction properly uses its cache system
        """
        # useful references and tools
        cache = LogItem.objects._cache
        curr_db = LogItem.objects.db
        from copy import deepcopy

        # clear cache
        LogItem.objects.clear_cache()

        # state should be empty
        state = deepcopy(cache)
        self.assertEqual(state, {})

        LogItem.objects.log_action(
            user = profile,
            affected_object = user,
            action = act1,
        )

        self.assertNotEqual(state, cache)

        # state should contain 1 LogAction
        state = deepcopy(cache)
        self.assertEqual(len(state[curr_db]), 1)

        LogItem.objects.log_action(
            user = profile,
            affected_object = user,
            action = "delete",
        )

        # state should still contain 1 LogAction
        # but cache should contain 2 LogActions
        self.assertEqual(len(state[curr_db]), 1)
        self.assertNotEqual(state, cache)

        # caching: state should be the same as cache
        state = deepcopy(cache)
        LogItem.objects.log_action(
            user = profile,
            affected_object = user,
            action = "delete",
        )
        self.assertEqual(state, cache)


        # both state and cache should be empty
        LogItem.objects.clear_cache()
        state = dict()
        self.assertEqual(state, cache)
