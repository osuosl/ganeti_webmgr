import unittest
from datetime import datetime

from django import forms

from muddle.core.models import PluginConfig
from muddle.core.plugins.plugin_manager import RootPluginManager
from muddle.core.plugins.models.form import *
from muddle.core.plugins.model_support import ModelManager, ModelWrapper
from muddle.tests.models import *

def suite():
    return unittest.TestSuite([
            unittest.TestLoader().loadTestsFromTestCase(Form_Simple_Test),
            unittest.TestLoader().loadTestsFromTestCase(Form_Child_Test),
            unittest.TestLoader().loadTestsFromTestCase(Form_Parent_Test),
            unittest.TestLoader().loadTestsFromTestCase(Form_One_To_One_Test),
            unittest.TestLoader().loadTestsFromTestCase(Form_One_To_Many_Test),
            unittest.TestLoader().loadTestsFromTestCase(Form_Many_To_One_Test),
            unittest.TestLoader().loadTestsFromTestCase(Form_Many_To_Many_Test),
        ])


class Form_Simple_Test(unittest.TestCase):

    def setUp(self):
        root = RootPluginManager()
        config = PluginConfig()
        manager = ModelManager(root, config)
        simple= ModelWrapper(Simple)
        manager.register(simple)
        view = ModelEditView(simple)
        self.attrs = view._get_form()
        self.klass = view.get_form()

    def tearDown(self):
        Simple.objects.all().delete()

    def test_form_structure(self):
        dict = self.attrs
        # field contents
        self.assert_('integer' in dict, dict)
        self.assert_('text' in dict, dict)
        self.assert_('char' in dict, dict)
        self.assert_('datetime' in dict, dict)
        self.assert_('date' in dict, dict)
        self.assert_('time' in dict, dict)
    
        # field types
        self.assert_(issubclass(dict['integer'].__class__,(forms.IntegerField,)), dict)
        self.assert_(issubclass(dict['text'].__class__,(forms.CharField,)), dict)
        self.assert_(issubclass(dict['char'].__class__,(forms.CharField,)), dict)
        self.assert_(issubclass(dict['datetime'].__class__,(forms.SplitDateTimeField,)), dict)
        self.assert_(issubclass(dict['date'].__class__,(forms.DateField,)), dict)
        self.assert_(issubclass(dict['time'].__class__,(forms.TimeField,)), dict)        
    
    def test_create(self):
        form = self.klass('abc')
        now = datetime.now()
        data = {
            'integer':123,
            'text':'abc',
            'char':'abc',
            'dateime':now,
            'date':now,
            'time':now,
        }
        form = self.klass(data)
        form.save()
    
    def test_update(self):
        now = datetime.now()
        data = {
            'id':1,
            'integer':123,
            'text':'abc',
            'char':'abc',
            'dateime':now,
            'date':now,
            'time':now,
        }
        simple = Simple()
        simple.__dict__.update(data)
        form = self.klass(simple.__dict__)
        form.save()
    
    def test_load(self):
        now = datetime.now()
        data = {
            'integer':123,
            'text':'abc',
            'char':'abc',
            'dateime':now,
            'date':now,
            'time':now,
            'url':'http://google.com'
        }
        form = self.klass(simple.__dict__)
    
    def test_permissions(self):
        pass
    
    
class Form_One_To_One_Test(unittest.TestCase):

    def setUp(self):
        root = RootPluginManager()
        config = PluginConfig()
        manager = ModelManager(root, config)
        parent = ModelWrapper(Complex)
        manager.register(parent)
        child = ModelWrapper(OneToOne)
        manager.register(child)
        view = ModelEditView(parent)
        self.attrs = view._get_form()
        self.klass = view.get_form()

    def test_form_structure(self):
        dict = self.attrs
        # field contents
        self.assert_('onetoone' in dict['one_to_one'], dict)

    def test_create(self):
        pass
    
    def test_save(self):
        pass
    
    def test_load(self):
        pass
    
    def test_permissions(self):
        pass
    
    
class Form_Parent_Test(unittest.TestCase):

    def setUp(self):
        root = RootPluginManager()
        config = PluginConfig()
        manager = ModelManager(root, config)
        parent = ModelWrapper(Extended)
        manager.register(parent)
        child = ModelWrapper(ChildA)
        manager.register(child)
        view = ModelEditView(parent)
        self.attrs = view._get_form()
        self.klass = view.get_form()

    def test_form_structure(self):
        dict = self.attrs
        # field contents
        self.assert_('a' in dict, dict)
        self.assert_('b' in dict, dict)

    def test_create(self):
        pass
    
    def test_save(self):
        pass
    
    def test_load(self):
        pass
    
    def test_permissions(self):
        pass
    
    
class Form_Child_Test(unittest.TestCase):

    def setUp(self):
        root = RootPluginManager()
        config = PluginConfig()
        manager = ModelManager(root, config)
        parent = ModelWrapper(Extended)
        manager.register(parent)
        child = ModelWrapper(ChildA)
        manager.register(child)
        view = ModelEditView(child)
        self.attrs = view._get_form()
        self.klass = view.get_form()

    def test_form_structure(self):
        dict = self.attrs
        # field contents
        self.assert_('a' in dict, dict)
        self.assert_('b' in dict, dict)

    def test_create(self):
        pass
    
    def test_save(self):
        pass
    
    def test_load(self):
        pass
    
    def test_permissions(self):
        pass

class Form_One_To_Many_Test(unittest.TestCase):

    def setup(self):
        root = RootPluginManager()
        config = PluginConfig()
        self.manager = ModelManager(root, config)

    def test_create(self):
        pass
    
    def test_save(self):
        pass
    
    def test_load(self):
        pass
    
    def test_permissions(self):
        pass
    
    
class Form_Many_To_One_Test(unittest.TestCase):

    def setup(self):
        root = RootPluginManager()
        config = PluginConfig()
        self.manager = ModelManager(root, config)

    def test_create(self):
        pass
    
    def test_save(self):
        pass
    
    def test_load(self):
        pass
    
    def test_permissions(self):
        pass
    
    
class Form_Many_To_Many_Test(unittest.TestCase):

    def setup(self):
        root = RootPluginManager()
        config = PluginConfig()
        self.manager = ModelManager(root, config)

    def test_create(self):
        pass
    
    def test_save(self):
        pass
    
    def test_load(self):
        pass
    
    def test_permissions(self):
        pass