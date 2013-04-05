from object_permissions import get_user_perms, grant

from ganeti_web.tests.views.virtual_machine.base import TestVirtualMachineViewsBase

__all__ = ['TestVirtualMachinePermissionsViews']


class TestVirtualMachinePermissionsViews(TestVirtualMachineViewsBase):

    def test_view_users(self):
        """
        Tests view for cluster users:

        Verifies:
            * lack of permissions returns 403
            * nonexistent Cluster returns 404
            * nonexistent VirtualMachine returns 404
        """
        url = "/cluster/%s/%s/users/"
        args = (self.cluster.slug, self.vm.hostname)
        self.validate_get(url, args, 'object_permissions/permissions/users.html')

    def test_view_add_permissions(self):
        """
        Test adding permissions to a new User or Group
        """
        url = '/cluster/%s/%s/permissions/'
        args = (self.cluster.slug, self.vm.hostname)

        # anonymous user
        response = self.c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assertTrue(self.c.login(username=self.user.username,
                                     password='secret'))
        response = self.c.get(url % args)
        self.assertEqual(403, response.status_code)

        # nonexisent cluster
        response = self.c.get(url % ("DOES_NOT_EXIST", self.vm.hostname))
        self.assertEqual(404, response.status_code)

        # nonexisent vm
        response = self.c.get(url % (self.cluster.slug, "DOES_NOT_EXIST"))
        self.assertEqual(404, response.status_code)

        # valid GET authorized user (perm)
        grant(self.user, 'admin', self.vm)
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')
        self.user.revoke('admin', self.vm)

        # valid GET authorized user (cluster admin)
        grant(self.user, 'admin', self.cluster)
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')
        self.user.revoke('admin', self.cluster)

        # valid GET authorized user (superuser)
        self.user.is_superuser = True
        self.user.save()
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')

        # no user or group
        data = {'permissions': ['admin'], 'obj': self.vm.pk}
        response = self.c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)

        # both user and group
        data = {'permissions': ['admin'], 'group': self.group.id,
                'user': self.user1.id, 'obj': self.vm.pk}
        response = self.c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)

        # no permissions specified - user
        data = {'permissions': [], 'user': self.user1.id, 'obj': self.vm.pk}
        response = self.c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)

        # no permissions specified - group
        data = {'permissions': [], 'group': self.group.id, 'obj': self.vm.pk}
        response = self.c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])

        # valid POST user has permissions
        self.user1.grant('power', self.vm)
        data = {'permissions': ['admin'], 'user': self.user1.id, 'obj': self.vm.pk}
        response = self.c.post(url % args, data)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'object_permissions/permissions/user_row.html')
        self.assertTrue(self.user1.has_perm('admin', self.vm))
        self.assertFalse(self.user1.has_perm('power', self.vm))

        # valid POST group has permissions
        self.group.grant('power', self.vm)
        data = {'permissions': ['admin'], 'group': self.group.id, 'obj': self.vm.pk}
        response = self.c.post(url % args, data)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'object_permissions/permissions/group_row.html')
        self.assertEqual(['admin'], self.group.get_perms(self.vm))

    def test_view_user_permissions(self):
        """
        Tests updating User's permissions

        Verifies:
            * anonymous user returns 403
            * lack of permissions returns 403
            * nonexistent cluster returns 404
            * invalid user returns 404
            * invalid group returns 404
            * missing user and group returns error as json
            * GET returns html for form
            * If user/group has permissions no html is returned
            * If user/group has no permissions a json response of -1 is returned
        """
        args = (self.cluster.slug, self.vm.hostname, self.user1.id)
        args_post = (self.cluster.slug, self.vm.hostname)
        url = "/cluster/%s/%s/permissions/user/%s"
        url_post = "/cluster/%s/%s/permissions/"

        # anonymous user
        response = self.c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assertTrue(self.c.login(username=self.user.username,
                                     password='secret'))
        response = self.c.get(url % args)
        self.assertEqual(403, response.status_code)

        # nonexisent cluster
        response = self.c.get(url % ("DOES_NOT_EXIST", self.vm.hostname,
                                     self.user1.id))
        self.assertEqual(404, response.status_code)

        # nonexisent vm
        response = self.c.get(url % (self.cluster.slug, "DOES_NOT_EXIST",
                                     self.user1.id))
        self.assertEqual(404, response.status_code)

        # valid GET authorized user (perm)
        grant(self.user, 'admin', self.vm)
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')
        self.user.revoke('admin', self.vm)

        # valid GET authorized user (cluster admin)
        grant(self.user, 'admin', self.cluster)
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')
        self.user.revoke('admin', self.cluster)

        # valid GET authorized user (superuser)
        self.user.is_superuser = True
        self.user.save()
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')

        # invalid user
        response = self.c.get(url % (self.cluster.slug, self.vm.hostname, -1))
        self.assertEqual(404, response.status_code)

        # invalid user (POST)
        self.user1.grant('power', self.vm)
        data = {'permissions': ['admin'], 'user': -1, 'obj': self.vm.pk}
        response = self.c.post(url_post % args_post, data)
        self.assertEqual('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)

        # no user (POST)
        self.user1.grant('power', self.vm)
        data = {'permissions': ['admin'], 'obj': self.vm.pk}
        response = self.c.post(url_post % args_post, data)
        self.assertEqual('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)

        # valid POST user has permissions
        self.user1.grant('power', self.vm)
        data = {'permissions': ['admin'], 'user': self.user1.id, 'obj': self.vm.pk}
        response = self.c.post(url_post % args_post, data)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'object_permissions/permissions/user_row.html')
        self.assertTrue(self.user1.has_perm('admin', self.vm))
        self.assertFalse(self.user1.has_perm('power', self.vm))

        # valid POST user has no permissions left
        data = {'permissions': [], 'user': self.user1.id, 'obj': self.vm.pk}
        response = self.c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        self.assertEqual([], get_user_perms(self.user, self.vm))
        self.assertEqual('"user_88"', response.content)

    def test_view_group_permissions(self):
        """
        Test editing Group permissions on a Cluster
        """
        args = (self.cluster.slug, self.vm.hostname, self.group.id)
        args_post = (self.cluster.slug, self.vm.hostname)
        url = "/cluster/%s/%s/permissions/group/%s"
        url_post = "/cluster/%s/%s/permissions/"

        # anonymous user
        response = self.c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assertTrue(self.c.login(username=self.user.username,
                                     password='secret'))
        response = self.c.get(url % args)
        self.assertEqual(403, response.status_code)

        # nonexisent cluster
        response = self.c.get(url % ("DOES_NOT_EXIST", self.vm.hostname, self.group.id))
        self.assertEqual(404, response.status_code)

        # nonexisent vm
        response = self.c.get(url % (self.cluster.slug, "DOES_NOT_EXIST", self.user1.id))
        self.assertEqual(404, response.status_code)

        # valid GET authorized user (perm)
        grant(self.user, 'admin', self.vm)
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')
        self.user.revoke('admin', self.vm)

        # valid GET authorized user (cluster admin)
        grant(self.user, 'admin', self.cluster)
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')
        self.user.revoke('admin', self.cluster)

        # valid GET authorized user (superuser)
        self.user.is_superuser = True
        self.user.save()
        response = self.c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')

        # invalid group
        response = self.c.get(url % (self.cluster.slug, self.vm.hostname, 0))
        self.assertEqual(404, response.status_code)

        # invalid group (POST)
        data = {'permissions': ['admin'], 'group': -1, 'obj': self.vm.pk}
        response = self.c.post(url_post % args_post, data)
        self.assertEqual('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)

        # no group (POST)
        data = {'permissions': ['admin'], 'obj': self.vm.pk}
        response = self.c.post(url_post % args_post, data)
        self.assertEqual('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)

        # valid POST group has permissions
        self.group.grant('power', self.vm)
        data = {'permissions': ['admin'], 'group': self.group.id, 'obj': self.vm.pk}
        response = self.c.post(url_post % args_post, data)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'object_permissions/permissions/group_row.html')
        self.assertEqual(['admin'], self.group.get_perms(self.vm))

        # valid POST group has no permissions left
        data = {'permissions': [], 'group': self.group.id, 'obj': self.vm.pk}
        response = self.c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        self.assertEqual([], self.group.get_perms(self.vm))
        self.assertEqual('"group_42"', response.content)
