from django.template.context import RequestContext
from django.test.client import RequestFactory

from muddle.slots import register, ContextSlat, SlotProcessor
from muddle.slots.shortcuts import muddled_response
from muddle.slots.tests.registration import SlotsTestsBase
from muddle.slots.tests import context as global_context

__all__ = ['SlotsResponseTests', 'SlotsProcessorTests']

CONTEXT = None

def foo(request):
    """ context processor for testing """
    return dict(foo=1, xoo=2)


def bar(request):
    """ context processor for testing """
    return dict(bar=3, xoo=4)


class SlotsResponseTests(SlotsTestsBase):

    def setUp(self):
        super(SlotsResponseTests, self).setUp()
        self.factory = RequestFactory()
        self.request = self.factory.get('/test/')

    def tearDown(self):
        super(SlotsResponseTests, self).tearDown()
        

    def test_basic(self):
        register('foo', ContextSlat(foo), ContextSlat(bar))
        response = muddled_response('foo', self.request, 'slots/tests/test.html')
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, global_context.CONTEXT.get('foo'))
        self.assertEqual(3, global_context.CONTEXT.get('bar'))
        self.assertEqual(4, global_context.CONTEXT.get('xoo'))
    
    def test_no_slot(self):
        response = muddled_response('foo', self.request, 'slots/tests/foo1.html')
        self.assertEqual(200, response.status_code)
    
    def test_no_slats(self):
        register('foo')
        response = muddled_response('foo', self.request, 'slots/tests/foo1.html')
        self.assertEqual(200, response.status_code)
    
    def test_with_context_instance(self):
        register('foo', ContextSlat(foo), ContextSlat(bar))
        context = RequestContext(self.request)
        response = muddled_response('foo', self.request, 'slots/tests/test.html', context_instance=context)
        self.assertEqual(200, response.status_code)
        self.assertEqual(1, global_context.CONTEXT.get('foo'))
        self.assertEqual(3, global_context.CONTEXT.get('bar'))
        self.assertEqual(4, global_context.CONTEXT.get('xoo'))
    
    def test_with_dictionary(self):
        register('foo', ContextSlat(foo), ContextSlat(bar))
        data = dict(xar=42, foo=42)
        response = muddled_response('foo', self.request, 'slots/tests/test.html', data)
        self.assertEqual(200, response.status_code)
        self.assertEqual(42, global_context.CONTEXT.get('xar'))
        self.assertEqual(42, global_context.CONTEXT.get('foo'))
    
    def test_with_context_and_dictionary(self):
        register('foo', ContextSlat(foo), ContextSlat(bar))
        context = RequestContext(self.request)
        data = dict(xar=42, foo=42)
        response = muddled_response('foo', self.request, 'slots/tests/test.html', data, context_instance=context)
        self.assertEqual(200, response.status_code)
        self.assertEqual(42, global_context.CONTEXT.get('xar'))
        self.assertEqual(42, global_context.CONTEXT.get('foo'))
        self.assertEqual(3, global_context.CONTEXT.get('bar'))
        self.assertEqual(4, global_context.CONTEXT.get('xoo'))

    
class SlotsProcessorTests(SlotsTestsBase):

    def setUp(self):
        super(SlotsProcessorTests, self).setUp()

    def test_trivial(self):
        register('foo', ContextSlat(foo))
        SlotProcessor('foo')

    def test_no_slot(self):
        sp = SlotProcessor('DOES_NOT_EXIST')
        self.assertEqual({}, sp(None))

    def test_no_slats(self):
        register('foo')
        sp = SlotProcessor('foo')
        self.assertEqual({}, sp(None))

    def test_single_slat(self):
        register('foo', ContextSlat(foo))
        sp = SlotProcessor('foo')
        self.assertEqual(dict(foo=1, xoo=2), sp(None))

    def test_multiple_slats(self):
        register('foo', ContextSlat(foo))
        register('foo', ContextSlat(bar))
        sp = SlotProcessor('foo')
        self.assertEqual(dict(foo=1, bar=3, xoo=4), sp(None))


