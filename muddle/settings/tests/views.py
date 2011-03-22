from django.test.client import Client
from django.contrib.auth.models import User
from muddle.settings import AppSettings

from muddle.settings.tests.usage import UsageBase, FOO_DATA

__all__ = ['CategoriesView', 'DetailView', 'SaveView']


class ViewBase(UsageBase):
    """ base for views, adds setup/teardown for users """
    url = ''
    args = tuple()
    c = Client()
    template = 'index.html'
    method = 'get'
    data = None

    def setUp(self):
        super(ViewBase, self).setUp()

        self.superuser, new = User.objects.get_or_create(username='superuser', is_superuser=True)
        self.unauthorized, new = User.objects.get_or_create(username='unauthorized')
        self.superuser.set_password('secret')
        self.unauthorized.set_password('secret')
        self.superuser.save()
        self.unauthorized.save()

    def tearDown(self):
        super(ViewBase, self).tearDown()
        self.c.logout()
        User.objects.all().delete()

    def execute(self, username='superuser', method=None, follow=True):
        """ logs in and executes the request """
        method = method if method else self.method
        self.assertTrue(self.c.login(username=username, password='secret'))
        method = getattr(self.c, method)
        url = self.url % self.args
        if self.data is None:
            return method(url, follow=follow)
        return method(url, self.data, follow=follow)


class DefaultViewBase(ViewBase):
    """ Base for get requests, adds some common tests """
    def test_anonymous(self):
        method = getattr(self.c, self.method)
        response = method(self.url % self.args, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertTemplateNotUsed(response, self.template)

    def test_unauthorized(self):
        response = self.execute('unauthorized')
        self.assertEqual(403, response.status_code)

    def test_authorized_superuser(self):
        response = self.execute()
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


class CategoriesView(DefaultViewBase):
    """ test loading list of top level setting categories """
    url = '/settings/'
    template = 'muddle/settings/categories.html'


class DetailView(DefaultViewBase):
    """ test loading the detail (edit) view for a top level category """
    url = '/settings/%s'
    args = ('general',)
    template = 'muddle/settings/detail.html'

    def test_form_loading(self):
        """ tests that the data for a form was properly loaded """
        response = self.execute()
        forms = response.context['forms']
        self.assertEqual(2, len(forms))
        self.assertTrue('foo' in forms)
        self.assertTrue('xoo' in forms)
        form = forms['foo']
        self.assertTrue(form.is_valid(), form.errors)
        form_data = forms['foo'].cleaned_data
        for k, v in FOO_DATA.items():
            self.assertEqual(v, form_data[k])


class SaveView(ViewBase):
    """
    Test Saving a settings subcategory
    """
    url = '/settings/%s/%s'
    args = ('general','foo')
    c = Client()
    method = 'post'
    data = dict(
        one=True,
        two='new two!',
        three='new three!',
        four=True,
    )
    
    def test_anonymous(self):
        response = self.c.post(self.url % self.args, self.data, follow=True)
        self.assertEqual(200, response.status_code)
        self.assertEqual('text/html; charset=utf-8', response['content-type'])

    def test_unauthorized(self):
        response = self.execute('unauthorized')
        self.assertEqual(403, response.status_code)

    def test_authorized_superuser(self):
        response = self.execute()
        self.assertEqual(200, response.status_code)
        self.assertEqual('application/json', response['content-type'])

    def test_get(self):
        response = self.execute(method='get')
        self.assertEqual(405, response.status_code)

    def test_data_successful(self):
        response = self.execute()
        self.assertEqual("1", response.content)
        
        foo = AppSettings.general.foo
        for k, v in self.data.items():
            self.assertEqual(v, getattr(foo, k))

        # three was not passed and should be removed from the database
        self.assertFalse(hasattr(foo, 'six'))