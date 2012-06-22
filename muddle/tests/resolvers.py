from django.test import TestCase

from muddle.core.resolvers.urls import register, resolve, smart_getattr
from muddle.models import TestModel, TestModelChild, TestModelChildChild

def noop_view(request):
    """ A fake view that doesn't actually do anything.  This is used for test
    url mappings that don't actually need a real view.  """
    pass


class TestUrlResolver(TestCase):

    def setUp(self):
        self.tearDown()

        self.parent = TestModel.objects.create(value=1, value2=2)
        self.child = TestModelChild.objects.create(value=3, value2=4,
                                                   parent=self.parent)
        self.childchild = TestModelChildChild.objects.create(value=5,
                                                             value2=6,
                                                             parent=self.child)

    def tearDown(self):
        TestModelChildChild.objects.all().delete()
        TestModelChild.objects.all().delete()
        TestModel.objects.all().delete()

    def test_register(self):
        register(TestModel, 'resolve-test-args', 'foo')
        register(TestModel, 'resolve-test-args', 'foo', 'bar')
        register(TestModel, 'resolve-test-kwargs', foo='foo')
        register(TestModel, 'resolve-test-kwargs', foo='foo', bar='bar')

        def fail():
            register(TestModel, 'resolve-test-mix', 'foo', bar='bar')
        self.assertRaises(ValueError, fail)

    def test_smart_get_attr(self):
        """
        Tests that smart get attr can retrieve attributes
        """
        # direct property
        self.assertEqual(1, smart_getattr(self.parent, 'value'))
        self.assertEqual(2, smart_getattr(self.parent, 'value2'))

        # 2 levels of objects
        self.assertEqual(3, smart_getattr(self.child, 'value'))
        self.assertEqual(4, smart_getattr(self.child, 'value2'))
        self.assertEqual(1, smart_getattr(self.child, 'parent.value'))
        self.assertEqual(2, smart_getattr(self.child, 'parent.value2'))

        # 3 levels of objects
        self.assertEqual(self.parent, smart_getattr(self.child, 'parent'))
        self.assertEqual(1, smart_getattr(self.childchild, 'parent.parent.value'))
        self.assertEqual(2, smart_getattr(self.childchild, 'parent.parent.value2'))
        self.assertEqual(self.parent, smart_getattr(self.childchild, 'parent.parent'))

        # default value
        self.assertEqual(99, smart_getattr(self.parent, 'doesnotexist', 99))
        self.assertEqual(99, smart_getattr(self.child, 'parent.doesnotexist', 99))
        self.assertEqual(99, smart_getattr(self.childchild, 'parent.self.parent.doesnotexist', 99))

        # missing property (no default)
        def fail():
            smart_getattr(self.parent, 'doesnotexist')

        def fail1():
            smart_getattr(self.child, 'parent.doesnotexist')

        def fail2():
            smart_getattr(self.childchild, 'parent.self.parent.doesnotexist')

        self.assertRaises(AttributeError, fail)
        self.assertRaises(AttributeError, fail1)
        self.assertRaises(AttributeError, fail2)

    def test_resolve_args(self):
        """
        Test resolving a detail url with args
        """
        register(TestModel, 'resolve-test-args', 'value', 'value2')
        register(TestModelChild, 'resolve-test-args', 'value', 'parent.value')
        self.assertEqual('/model_resolve_test/1/2/', resolve(self.parent))
        self.assertEqual('/model_resolve_test/3/1/', resolve(self.child))

    def test_resolve_kwargs(self):
        """
        Test resolving a detail url with kwargs
        """
        register(TestModel, 'resolve-test-kwargs', one='value', two='value2')
        register(TestModelChild, 'resolve-test-kwargs', one='value', two='parent.value')
        self.assertEqual('/model_resolve_test/1/2/', resolve(self.parent))
        self.assertEqual('/model_resolve_test/3/1/', resolve(self.child))
