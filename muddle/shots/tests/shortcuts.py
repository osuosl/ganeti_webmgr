from django.contrib.auth.models import User
from django.template.context import RequestContext
from django.test.client import RequestFactory

from muddle.shots import register, ContextMixer
from muddle.shots.tests.registration import ShotsTestsBase
from muddle.shots.tests import context as global_context

__all__ = ['ShotsResponseTests', 'ShotsProcessorTests']

CONTEXT = None

def foo(request):
    """ context processor for testing """
    return dict(foo=1, xoo=2)


def bar(request):
    """ context processor for testing """
    return dict(bar=3, xoo=4)


class ShotsResponseTests(ShotsTestsBase):

    def setUp(self):
        super(ShotsResponseTests, self).setUp()
        self.factory = RequestFactory()
        self.request = self.factory.get('/test/')
        self.request.user = User.objects.create(username='tester')

    def tearDown(self):
        User.objects.all().delete()

    def test_with_context_instance(self):
        register('foo', ContextMixer(foo), ContextMixer(bar))
        context = RequestContext(self.request)
        self.assertEqual(1, global_context.CONTEXT.get('foo'))
        self.assertEqual(3, global_context.CONTEXT.get('bar'))
        self.assertEqual(4, global_context.CONTEXT.get('xoo'))

    def test_with_dictionary(self):
        register('foo', ContextMixer(foo), ContextMixer(bar))
        data = dict(xar=42, foo=42)
        self.assertEqual(42, global_context.CONTEXT.get('xar'))
        self.assertEqual(42, global_context.CONTEXT.get('foo'))

    def test_with_context_and_dictionary(self):
        register('foo', ContextMixer(foo), ContextMixer(bar))
        context = RequestContext(self.request)
        data = dict(xar=42, foo=42)
        self.assertEqual(42, global_context.CONTEXT.get('xar'))
        self.assertEqual(42, global_context.CONTEXT.get('foo'))
        self.assertEqual(3, global_context.CONTEXT.get('bar'))
        self.assertEqual(4, global_context.CONTEXT.get('xoo'))
