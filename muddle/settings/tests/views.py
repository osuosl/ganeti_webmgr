from django.test.client import Client
from django.contrib.auth.models import User
from muddle.settings import AppSettings
from muddle.settings.models import AppSettingsCategory, AppSettingsValue

from muddle.settings.tests.usage import AppSettingsUsageBase

__all__ = ['SettingsCategoriesView', 'SettingsDetailView', 'SettingsSaveView']

class SettingsViewBase(AppSettingsUsageBase):
    url = ''
    args = tuple()
    c = Client()
    template = 'index.html'
    method = 'get'

    def setUp(self):
        super(SettingsViewBase, self).setUp()

        self.superuser, new = User.objects.get_or_create(username='superuser', is_superuser=True)
        self.unauthorized, new = User.objects.get_or_create(username='unauthorized')
        self.superuser.set_password('secret')
        self.unauthorized.set_password('secret')
        self.superuser.save()
        self.unauthorized.save()

    def tearDown(self):
        super(SettingsViewBase, self).tearDown()
        self.c.logout()
        User.objects.all().delete()

    def test_anonymous(self):
        method = getattr(self.c, self.method)
        response = method(self.url % self.args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateNotUsed(response, self.template)

    def test_unauthorized(self):
        self.assertTrue(self.c.login(username='unauthorized', password='secret'))
        method = getattr(self.c, self.method)
        response = method(self.url % self.args)
        self.assertEqual(403, response.status_code)

    def test_authorized_superuser(self):
        self.assertTrue(self.c.login(username='superuser', password='secret'))
        method = getattr(self.c, self.method)
        response = method(self.url % self.args)
        self.assertEqual(200, response.status_code)
        self.assertTemplateUsed(response, self.template)

    def assert_404(self):
        """ tests all possible 404 conditions based on args """
        for i in range(len(self.args)):
            args = list(self.args)
            args[i] = '-1'
            args = tuple(args)
            method = getattr(self.c, self.method)
            self.assertEqual(404, method(self.url % args).status_code)

class SettingsCategoriesView(SettingsViewBase):
    """ test loading list of top level setting categories """
    url = '/settings/'
    template = 'muddle/settings/categories.html'


class SettingsDetailView(SettingsViewBase):
    """ test loading the detail (edit) view for a top level category """
    url = '/settings/%s'
    args = ('general',)

class SettingsSaveView(SettingsViewBase):
    """
    Test Saving a settings subcategory
    """
    url = '/settings/%s/%s'
    args = ('general','foo')
    c = Client()
    method = 'post'

    def test_post_only(self):
        self.assertTrue(self.c.login(username='superuser', password='secret'))
        self.assertEqual(405, self.c.get(self.url % self.args).status_code)
