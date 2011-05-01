from object_permissions import get_user_perms, grant

from ganeti.tests.views.virtual_machine.base import TestVirtualMachineViewsBase

__all__ = ['TestVirtualMachinePermissionsViews']

global user, user1, group
global c, cluster, vm


class TestVirtualMachinePermissionsViews(TestVirtualMachineViewsBase):

    context = globals()

    def test_view_users(self):
        """
        Tests view for cluster users:

        Verifies:
            * lack of permissions returns 403
            * nonexistent Cluster returns 404
            * nonexistent VirtualMachine returns 404
        """
        url = "/cluster/%s/%s/users/"
        args = (cluster.slug, vm.hostname)
        self.validate_get(url, args, 'object_permissions/permissions/users.html')

    def test_view_add_permissions(self):
        """
        Test adding permissions to a new User or Group
        """
        url = '/cluster/%s/%s/permissions/'
        args = (cluster.slug, vm.hostname)

        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)

        # nonexisent cluster
        response = c.get(url % ("DOES_NOT_EXIST", vm.hostname))
        self.assertEqual(404, response.status_code)

        # nonexisent vm
        response = c.get(url % (cluster.slug, "DOES_NOT_EXIST"))
        self.assertEqual(404, response.status_code)

        # valid GET authorized user (perm)
        grant(user, 'admin', vm)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')
        user.revoke('admin', vm)

        # valid GET authorized user (cluster admin)
        grant(user, 'admin', cluster)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')
        user.revoke('admin', cluster)

        # valid GET authorized user (superuser)
        user.is_superuser = True
        user.save()
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')

        # no user or group
        data = {'permissions':['admin'], 'obj':vm.pk}
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)

        # both user and group
        data = {'permissions':['admin'], 'group':group.id, 'user':user1.id, 'obj':vm.pk}
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)

        # no permissions specified - user
        data = {'permissions':[], 'user':user1.id, 'obj':vm.pk}
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)

        # no permissions specified - group
        data = {'permissions':[], 'group':group.id, 'obj':vm.pk}
        response = c.post(url % args, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])

        # valid POST user has permissions
        user1.grant('power', vm)
        data = {'permissions':['admin'], 'user':user1.id, 'obj':vm.pk}
        response = c.post(url % args, data)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'object_permissions/permissions/user_row.html')
        self.assert_(user1.has_perm('admin', vm))
        self.assertFalse(user1.has_perm('power', vm))

        # valid POST group has permissions
        group.grant('power', vm)
        data = {'permissions':['admin'], 'group':group.id, 'obj':vm.pk}
        response = c.post(url % args, data)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'object_permissions/permissions/group_row.html')
        self.assertEqual(['admin'], group.get_perms(vm))

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
        args = (cluster.slug, vm.hostname, user1.id)
        args_post = (cluster.slug, vm.hostname)
        url = "/cluster/%s/%s/permissions/user/%s"
        url_post = "/cluster/%s/%s/permissions/"

        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)

        # nonexisent cluster
        response = c.get(url % ("DOES_NOT_EXIST", vm.hostname, user1.id))
        self.assertEqual(404, response.status_code)

        # nonexisent vm
        response = c.get(url % (cluster.slug, "DOES_NOT_EXIST", user1.id))
        self.assertEqual(404, response.status_code)

        # valid GET authorized user (perm)
        grant(user, 'admin', vm)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')
        user.revoke('admin', vm)

        # valid GET authorized user (cluster admin)
        grant(user, 'admin', cluster)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')
        user.revoke('admin', cluster)

        # valid GET authorized user (superuser)
        user.is_superuser = True
        user.save()
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')

        # invalid user
        response = c.get(url % (cluster.slug, vm.hostname, -1))
        self.assertEqual(404, response.status_code)

        # invalid user (POST)
        user1.grant('power', vm)
        data = {'permissions':['admin'], 'user':-1, 'obj':vm.pk}
        response = c.post(url_post % args_post, data)
        self.assertEqual('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)

        # no user (POST)
        user1.grant('power', vm)
        data = {'permissions':['admin'], 'obj':vm.pk}
        response = c.post(url_post % args_post, data)
        self.assertEqual('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)

        # valid POST user has permissions
        user1.grant('power', vm)
        data = {'permissions':['admin'], 'user':user1.id, 'obj':vm.pk}
        response = c.post(url_post % args_post, data)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'object_permissions/permissions/user_row.html')
        self.assert_(user1.has_perm('admin', vm))
        self.assertFalse(user1.has_perm('power', vm))

        # valid POST user has no permissions left
        data = {'permissions':[], 'user':user1.id, 'obj':vm.pk}
        response = c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        self.assertEqual([], get_user_perms(user, vm))
        self.assertEqual('"user_88"', response.content)

    def test_view_group_permissions(self):
        """
        Test editing Group permissions on a Cluster
        """
        args = (cluster.slug, vm.hostname, group.id)
        args_post = (cluster.slug, vm.hostname)
        url = "/cluster/%s/%s/permissions/group/%s"
        url_post = "/cluster/%s/%s/permissions/"

        # anonymous user
        response = c.get(url % args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'registration/login.html')

        # unauthorized user
        self.assert_(c.login(username=user.username, password='secret'))
        response = c.get(url % args)
        self.assertEqual(403, response.status_code)

        # nonexisent cluster
        response = c.get(url % ("DOES_NOT_EXIST", vm.hostname, group.id))
        self.assertEqual(404, response.status_code)

        # nonexisent vm
        response = c.get(url % (cluster.slug, "DOES_NOT_EXIST", user1.id))
        self.assertEqual(404, response.status_code)

        # valid GET authorized user (perm)
        grant(user, 'admin', vm)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')
        user.revoke('admin', vm)

        # valid GET authorized user (cluster admin)
        grant(user, 'admin', cluster)
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')
        user.revoke('admin', cluster)

        # valid GET authorized user (superuser)
        user.is_superuser = True
        user.save()
        response = c.get(url % args)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, 'object_permissions/permissions/form.html')

        # invalid group
        response = c.get(url % (cluster.slug, vm.hostname, 0))
        self.assertEqual(404, response.status_code)

        # invalid group (POST)
        data = {'permissions':['admin'], 'group':-1, 'obj':vm.pk}
        response = c.post(url_post % args_post, data)
        self.assertEqual('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)

        # no group (POST)
        data = {'permissions':['admin'], 'obj':vm.pk}
        response = c.post(url_post % args_post, data)
        self.assertEqual('application/json', response['content-type'])
        self.assertNotEqual('0', response.content)

        # valid POST group has permissions
        group.grant('power', vm)
        data = {'permissions':['admin'], 'group':group.id, 'obj':vm.pk}
        response = c.post(url_post % args_post, data)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])
        self.assertTemplateUsed(response, 'object_permissions/permissions/group_row.html')
        self.assertEqual(['admin'], group.get_perms(vm))

        # valid POST group has no permissions left
        data = {'permissions':[], 'group':group.id, 'obj':vm.pk}
        response = c.post(url_post % args_post, data)
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])
        self.assertEqual([], group.get_perms(vm))
        self.assertEqual('"group_42"', response.content)