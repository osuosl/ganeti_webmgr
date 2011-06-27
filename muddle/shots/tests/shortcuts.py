from django.contrib.auth.models import User
from django.template.context import RequestContext
from django.test.client import RequestFactory

from muddle.shots import register, ContextMixer, ShotProcessor
from muddle.shots.shortcuts import muddled_response
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

    def test_basic(self):
        register('foo', ContextMixer(foo), ContextMixer(bar))
        response = muddled_response('foo', self.request, 'shots/tests/test.html')
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, global_context.CONTEXT.get('foo'))
        self.assertEqual(3, global_context.CONTEXT.get('bar'))
        self.assertEqual(4, global_context.CONTEXT.get('xoo'))
    
    def test_no_shot(self):
        response = muddled_response('foo', self.request, 'shots/tests/foo1.html')
        self.assertEqual(200, response.status_code)
    
    def test_no_mixers(self):
        register('foo')
        response = muddled_response('foo', self.request, 'shots/tests/foo1.html')
        self.assertEqual(200, response.status_code)
    
    def test_with_context_instance(self):
        register('foo', ContextMixer(foo), ContextMixer(bar))
        context = RequestContext(self.request)
        response = muddled_response('foo', self.request, 'shots/tests/test.html', context_instance=context)
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, global_context.CONTEXT.get('foo'))
        self.assertEqual(3, global_context.CONTEXT.get('bar'))
        self.assertEqual(4, global_context.CONTEXT.get('xoo'))
    
    def test_with_dictionary(self):
        register('foo', ContextMixer(foo), ContextMixer(bar))
        data = dict(xar=42, foo=42)
        response = muddled_response('foo', self.request, 'shots/tests/test.html', data)
        self.assertEqual(200, response.status_code)
        self.assertEqual(42, global_context.CONTEXT.get('xar'))
        self.assertEqual(42, global_context.CONTEXT.get('foo'))
    
    def test_with_context_and_dictionary(self):
        register('foo', ContextMixer(foo), ContextMixer(bar))
        context = RequestContext(self.request)
        data = dict(xar=42, foo=42)
        response = muddled_response('foo', self.request, 'shots/tests/test.html', data, context_instance=context)
        self.assertEqual(200, response.status_code)
        self.assertEqual(42, global_context.CONTEXT.get('xar'))
        self.assertEqual(42, global_context.CONTEXT.get('foo'))
        self.assertEqual(3, global_context.CONTEXT.get('bar'))
        self.assertEqual(4, global_context.CONTEXT.get('xoo'))

    
class ShotsProcessorTests(ShotsTestsBase):

    def setUp(self):
        super(ShotsProcessorTests, self).setUp()

    def test_trivial(self):
        register('foo', ContextMixer(foo))
        ShotProcessor('foo')

    def test_no_shot(self):
        sp = ShotProcessor('DOES_NOT_EXIST')
        self.assertEqual({}, sp(None))

    def test_no_mixers(self):
        register('foo')
        sp = ShotProcessor('foo')
        self.assertEqual({}, sp(None))

    def test_single_mixer(self):
        register('foo', ContextMixer(foo))
        sp = ShotProcessor('foo')
        self.assertEqual(dict(foo=1, xoo=2), sp(None))

    def test_multiple_mixers(self):
        register('foo', ContextMixer(foo))
        register('foo', ContextMixer(bar))
        sp = ShotProcessor('foo')
        self.assertEqual(dict(foo=1, bar=3, xoo=4), sp(None))


