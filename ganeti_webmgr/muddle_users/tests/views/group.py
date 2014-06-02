from django.conf import settings
from django.contrib.auth.models import User, Group
from django.test import TestCase, Client

from object_permissions.registration import grant, revoke
from object_permissions.signals import view_add_user, view_remove_user

from ganeti_webmgr.muddle_users.signals import (view_group_edited, view_group_created,
                                  view_group_deleted)

class TestGroupViews(TestCase):

    def setUp(self):
        self.anonymous = User(id=1, username='anonymous')
        self.anonymous.save()
        settings.ANONYMOUS_USER_ID = 1

        self.user0 = User(id=2, username='tester0')
        self.user0.set_password('secret')
        self.user0.save()
        self.user1 = User(id=3, username='tester1')
        self.user1.set_password('secret')
        self.user1.save()

    def tearDown(self):
        self.anonymous.delete()
        self.user0.delete()
        self.user1.delete()

    def test_save(self, name='test'):
        """ Test saving an Group """
        group = Group(name=name)
        group.save()
        return group

    def test_view_list(self):
        """
        Test viewing list of Groups
        """
        group = self.test_save()
        group0 = self.test_save(name='group1')
        group1 = self.test_save(name='group2')
        group2 = self.test_save(name='group3')
        c = Client()
        url = '/groups/'

        # anonymous user
        response = c.get(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user (user with admin on no groups)
        self.assertTrue(c.login(username=self.user0.username, password='secret'))
        response = c.get(url)
        self.assertEqual(403, response.status_code)

        # authorized (permission)
        self.user0.grant('admin', group)
        self.user0.grant('admin', group1)
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'group/list.html')
        groups = response.context['groups']
        self.assertTrue(group in groups)
        self.assertTrue(group1 in groups)
        self.assertEqual(2, len(groups))

        # authorized (superuser)
        self.user0.revoke('admin', group0)
        self.user0.revoke('admin', group1)
        self.user0.is_superuser = True
        self.user0.save()
        response = c.get(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'group/list.html')
        groups = response.context['groups']
        self.assertTrue(group in groups)
        self.assertTrue(group0 in groups)
        self.assertTrue(group1 in groups)
        self.assertTrue(group2 in groups)
        self.assertEqual(4, len(groups))

    def test_view_detail(self):
        """
        Test Viewing the detail for a Group

        Verifies:
            * 200 returned for valid group
            * 404 returned for invalid group
        """
        group = self.test_save()
        c = Client()
        url = '/group/%s/'
        args = group.id

        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assertTrue(c.login(username=self.user0.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)

        # invalid user group
        response = c.get(url % "DoesNotExist")
        self.assertEqual(404, response.status_code)

        # authorized (permission)
        grant(self.user0, 'admin', group)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'group/detail.html')

        # authorized (superuser)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'group/detail.html')

    def test_view_edit(self):
        group = self.test_save()
        c = Client()
        url = '/group/%s/edit/'

        # anonymous user
        response = c.post(url % group.id, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assertTrue(c.login(username=self.user0.username, password='secret'))
        response = c.post(url % group.id)
        self.assertEqual(403, response.status_code)

        # invalid group
        response = c.post(url % "DoesNotExist")
        self.assertEqual(404, response.status_code)

        # get form - authorized (permission)
        # XXX need to implement Class wide permission for creating editing groups
        #grant(user, 'admin', group)
        #response = c.post(url % group.id)
        #self.assertEqual(200, response.status_code)
        #self.assertEquals('text/html; charset=utf-8', response['content-type'])
        #self.assertTemplateUsed(response, 'group/edit.html')

        # get form - authorized (permission)
        grant(self.user0, 'admin', group)
        response = c.post(url % group.id)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'group/edit.html')

        # get form - authorized (superuser)
        self.user0.revoke('admin', group)
        self.user0.is_superuser = True
        self.user0.save()
        response = c.post(url % group.id)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'group/edit.html')

        # missing name
        data = {'id':group.id}
        response = c.post(url % group.id, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])

        # setup signal
        self.signal_editor = self.signal_group = None
        def callback(sender, editor, **kwargs):
            self.signal_user = self.user0
            self.signal_group = sender
        view_group_edited.connect(callback)

        # successful edit
        data = {'id':group.id, 'name':'EDITED_NAME'}

        response = c.post(url % group.id, data)
        self.assertRedirects(response, '/group/%s' % group.pk)
        group = Group.objects.get(id=group.id)
        self.assertEqual('EDITED_NAME', group.name)

        # check signal set properties
        self.assertEqual(group, self.signal_group)
        self.assertEqual(self.user0, self.signal_user)

    def test_view_create(self):
        """
        Test creating a new Group
        """
        group = self.test_save()
        c = Client()
        url = '/group/add/'

        # anonymous user
        response = c.post(url, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assertTrue(c.login(username=self.user0.username, password='secret'))
        response = c.post(url)
        self.assertEqual(403, response.status_code)

        # get form - authorized (permission)
        # XXX need to implement Class level permissions
        #grant(user, 'admin', group)
        #response = c.post(url % group.id)
        #self.assertEqual(200, response.status_code)
        #self.assertEquals('text/html; charset=utf-8', response['content-type'])
        #self.assertTemplateUsed(response, 'group/edit.html')

        # get form - authorized (superuser)
        self.user0.revoke('admin', group)
        self.user0.is_superuser = True
        self.user0.save()
        response = c.post(url)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'group/edit.html')

        # missing name
        response = c.post(url, {'name':''})
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'group/edit.html')

        # setup signal
        self.signal_editor = self.signal_group = None
        def callback(sender, editor, **kwargs):
            self.signal_user = self.user0
            self.signal_group = sender
        view_group_created.connect(callback)

        # successful edit
        data = {'name':'ADD_NEW_GROUP'}
        response = c.post(url, data)
        group = Group.objects.get(name='ADD_NEW_GROUP')
        self.assertRedirects(response, '/group/%s' % group.pk)

        self.assertTrue(Group.objects.filter(name='ADD_NEW_GROUP').exists())

        # check signal set properties
        self.assertEqual(group, self.signal_group)
        self.assertEqual(self.user0, self.signal_user)

    def test_view_delete(self):
        """
        Test deleting a group

        Verifies:
            * group is deleted
            * all associated permissions are deleted
        """
        group0 = self.test_save()
        group1 = self.test_save(name='test2')
        c = Client()
        url = '/group/%s/edit/'

        # anonymous user
        response = c.delete(url % group0.id, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assertTrue(c.login(username=self.user0.username, password='secret'))
        response = c.delete(url % group0.id)
        self.assertEqual(403, response.status_code)

        # invalid group
        response = c.delete(url % "DoesNotExist")
        self.assertEqual(404, response.status_code)

        # get form - authorized (permission)
        grant(self.user0, 'admin', group0)
        response = c.delete(url % group0.id)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertFalse(Group.objects.filter(id=group0.id).exists())
        self.assertEqual('1', response.content)

        # setup signal
        self.signal_editor = self.signal_group = None
        def callback(sender, editor, **kwargs):
            self.signal_user = self.user0
            self.signal_group = sender
        view_group_deleted.connect(callback)

        # get form - authorized (superuser)
        self.user0.is_superuser = True
        self.user0.save()
        response = c.delete(url % group1.id)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertFalse(Group.objects.filter(id=group1.id).exists())
        self.assertEqual('1', response.content)

        # check signal set properties
        self.assertEqual(group1.name, self.signal_group.name)
        self.assertEqual(self.user0, self.signal_user)

    def test_view_add_user(self):
        """
        Test view for adding a user:

        Verifies:
            * request from unauthorized user results in 403
            * GET returns a 200 code, response is html
            * POST with a user id adds user, response is html for user
            * POST without user id returns error as json
            * POST for invalid user id returns error as json
            * adding user a second time returns error as json
        """
        group = self.test_save()
        c = Client()
        url = '/group/%d/user/add/'
        args = group.id

        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized
        self.assertTrue(c.login(username=self.user0.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)
        response = c.post(url % args)
        self.assertEqual(403, response.status_code)

        # authorized get (perm granted)
        grant(self.user0, 'admin', group)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'group/add_user.html')

        # authorized get (superuser)
        revoke(self.user0, 'admin', group)
        self.user0.is_superuser = True
        self.user0.save()
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'group/add_user.html')

        # missing user id
        response = c.post(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])

        # invalid user
        response = c.post(url % args, {'user':0})
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])

        # setup signal
        self.signal_sender = self.signal_user = self.signal_obj = None
        def callback(sender, user, obj, **kwargs):
            self.signal_sender = sender
            self.signal_user = user
            self.signal_obj = obj
        view_add_user.connect(callback)

        # valid post
        data = {'user':self.user0.id}
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'group/user_row.html')
        self.assertTrue(group.user_set.filter(id=self.user0.id).exists())

        # check signal fired
        self.assertEqual(self.signal_sender, self.user0)
        self.assertEqual(self.signal_user, self.user0)
        self.assertEqual(self.signal_obj, group)
        view_add_user.disconnect(callback)

        # same user again
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertEquals(group.user_set.filter(id=self.user0.id).count(), 1)

    def test_view_remove_user(self):
        """
        Test view for adding a user:

        Verifies:
            * GET redirects user to 405
            * POST with a user id remove user, returns 1
            * POST without user id returns error as json
            * users lacking perms receive 403
            * removing user not in group returns error as json
            * removing user that does not exist returns error as json
            * user loses all permissions when removed from group
        """
        group = self.test_save()
        c = Client()
        group.user_set.add(self.user0)
        url = '/group/%d/user/remove/'
        args = group.id

        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # invalid permissions
        self.assertTrue(c.login(username=self.user0.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)
        response = c.post(url % args)
        self.assertEqual(403, response.status_code)

        # authorize and login
        grant(self.user0, 'admin', group)

        # invalid method
        response = c.get(url % args)
        self.assertEqual(405, response.status_code)

        # valid request (perm)
        data = {'user':self.user0.id}
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertEqual('1', response.content)
        self.assertFalse(group.user_set.filter(id=self.user0.id).exists())
        self.assertEqual([], self.user0.get_perms(group))

        # setup signal
        self.signal_sender = self.signal_user = self.signal_obj = None
        def callback(sender, user, obj, **kwargs):
            self.signal_sender = sender
            self.signal_user = user
            self.signal_obj = obj
        view_remove_user.connect(callback)

        # valid request (superuser)
        revoke(self.user0, 'admin', group)
        self.user0.is_superuser = True
        self.user0.save()
        group.user_set.add(self.user0)
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertEqual('1', response.content)
        self.assertFalse(group.user_set.filter(id=self.user0.id).exists())

        # check signal fired
        self.assertEqual(self.signal_sender, self.user0)
        self.assertEqual(self.signal_user, self.user0)
        self.assertEqual(self.signal_obj, group)
        view_remove_user.disconnect(callback)

        # remove user again
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertFalse(group.user_set.filter(id=self.user0.id).exists())
        self.assertNotEqual('1', response.content)

        # remove invalid user
        response = c.post(url % args, {'user':0})
        self.assertEqual(200, response.status_code)
        self.assertEquals('application/json', response['content-type'])
        self.assertNotEqual('1', response.content)
