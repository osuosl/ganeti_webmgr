import unittest
from datetime import datetime

from django import forms

from muddle.models import PluginConfig
from muddle.plugins.managers.model_manager import ModelManager
from muddle.plugins.managers.root_plugin_manager import RootPluginManager
from muddle.plugins.models.form import *
from muddle.plugins.models.wrapper import  ModelWrapper
from test_app.models import *

def suite():
    return unittest.TestSuite([
            unittest.TestLoader().loadTestsFromTestCase(Form_Simple_Test),
            unittest.TestLoader().loadTestsFromTestCase(Form_Child_Test),
            unittest.TestLoader().loadTestsFromTestCase(Form_Parent_Test),
            unittest.TestLoader().loadTestsFromTestCase(Form_Parent_Depth_Test),
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
        simple= ModelWrapper(FieldTest)
        manager.register(simple)
        view = ModelEditView(simple)
        self.attrs = view.get_fields(simple)
        self.klass = view.get_form()

    def tearDown(self):
        FieldTest.objects.all().delete()

    def test_form_structure(self):
        """
        Tests:
            * all model properties are added to form
            * form fields have default type
        """
        dict = self.klass.form.base_fields
        
        # field contents
        self.assert_('integer' in dict, dict)
        self.assert_('text' in dict, dict)
        self.assert_('char' in dict, dict)
        self.assert_('pk' in dict, dict)
        #self.assert_('datetime' in dict, dict)
        #self.assert_('date' in dict, dict)
        #self.assert_('time' in dict, dict)
    
        # field types
        self.assert_(issubclass(dict['integer'].__class__,(forms.IntegerField,)), dict)
        self.assert_(issubclass(dict['text'].__class__,(forms.CharField,)), dict)
        self.assert_(issubclass(dict['char'].__class__,(forms.CharField,)), dict)
        self.assert_(issubclass(dict['pk'].__class__,(forms.IntegerField,)), dict)
        #self.assert_(issubclass(dict['datetime'].__class__,(forms.SplitDateTimeField,)), dict)
        #self.assert_(issubclass(dict['date'].__class__,(forms.DateField,)), dict)
        #self.assert_(issubclass(dict['time'].__class__,(forms.TimeField,)), dict)
    
    def test_create(self):
        self.assert_(len(FieldTest.objects.all())==0, len(FieldTest.objects.all()))
        form = self.klass()
        now = datetime.now()
        data = {
            'integer':123,
            'text':'abc',
            'char':'abc',
        }
        form = self.klass(data)
        form.save()
        query = FieldTest.objects.all()
        self.assert_(len(query)==1, len(query))
        simple = query[0]
        for k,v in data.items():
            self.assert_(simple.__dict__[k]==v, (simple.__dict__[k], v))
        
    
    def test_update(self):
        self.assert_(len(FieldTest.objects.all())==0, len(FieldTest.objects.all()))
        now = datetime.now()
        data = {
            'pk':1,
            'integer':123,
            'text':'abc',
            'char':'def'
        }
        simple = FieldTest()
        simple.__dict__.update(data)
        simple.id = 1
        simple.save()
        data = {
            'pk':1,
            'integer':456,
            'text':'ghi',
            'char':'jkl',
        }
        form = self.klass(data)
        form.save()
        query = FieldTest.objects.all()
        self.assert_(len(query)==1, len(query))
        simple = query[0]
        for k,v in data.items():
            k = 'id' if k == 'pk' else k
            self.assert_(simple.__getattribute__(k)==v, (simple.__dict__[k], v))
    
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

    def tearDown(self):
        OneToOne.objects.all().delete()
        Complex.objects.all().delete()

    def test_form_structure(self):
        dict = self.attrs
        # field contents
        self.assert_('onetoone' in dict['one_to_one'], dict)

    def test_create(self):
        self.assert_(len(Complex.objects.all())==0, len(Complex.objects.all()))
        self.assert_(len(OneToOne.objects.all())==0, len(OneToOne.objects.all()))
        form = self.klass({'a':1,'onetoone_b':2})
        form.save()
        self.assert_(len(Complex.objects.all())==1, len(Complex.objects.all()))
        self.assert_(len(OneToOne.objects.all())==1, len(OneToOne.objects.all()))
        parent = Complex.objects.all()[0]
        child = OneToOne.objects.all()[0]
        self.assert_(parent.onetoone.id==child.id, (parent.onetoone.id,child.id))
        self.assert_(child.complex.id==parent.id, (child.complex.id, parent.id))
    
    def test_update(self):
        self.assert_(len(Complex.objects.all())==0, len(Complex.objects.all()))
        self.assert_(len(OneToOne.objects.all())==0, len(OneToOne.objects.all()))
        parent = Complex()
        parent.a=3
        parent.id=1
        parent.save()
        child = OneToOne()
        child.b=4
        child.complex = parent
        child.save()
        form = self.klass({'pk':1, 'a':5, 'onetoone_b':6})
        form.save()
        parent = Complex.objects.get(id=1)
        child = parent.onetoone
        self.assert_(parent.a==5, parent.a)
        self.assert_(child.b==6, child.b)
        
    
    def test_permissions(self):
        pass
    
    
class Form_Parent_Test(unittest.TestCase):
    """
    Tests for models that have children
    """
    def setUp(self):
        root = RootPluginManager()
        config = PluginConfig()
        manager = ModelManager(root, config)
        parent = ModelWrapper(Extended)
        manager.register(parent)
        child = ModelWrapper(ChildA)
        manager.register(child)
        view = ModelEditView(parent)
        self.klass = view.get_form()
        self.attrs = view.get_fields(parent)

    def tearDown(self):
        Extended.objects.all().delete()
        ChildA.objects.all().delete()
        ChildB.objects.all().delete()

    def test_form_structure(self):
        dict = self.attrs
        form = self.klass.form
        # field contents
        self.assert_(issubclass(form,(ParentBase,)), form)
        self.assert_(len(form.children)==1,form.children)
        self.assert_('ChildA' in form.children, form.children)
        self.assert_(len(form.recurse)==0, form.recurse)
        self.assert_('a' in dict, dict)

    def test_create_parent(self):
        self.assert_(len(Extended.objects.all())==0, len(Extended.objects.all()))
        self.assert_(len(ChildA.objects.all())==0, len(ChildA.objects.all()))
        self.assert_(len(ChildB.objects.all())==0, len(ChildB.objects.all()))
        form = self.klass({'_selected_child':'', 'a':5})
        form.save()
        self.assert_(len(Extended.objects.all())==1, len(Extended.objects.all()))
        self.assert_(len(ChildA.objects.all())==0, len(ChildA.objects.all()))
        self.assert_(len(ChildB.objects.all())==0, len(ChildB.objects.all()))
        parent = Extended.objects.all()[0]
        self.assert_(parent.a==5, parent.a)

    def test_create_child(self):
        self.assert_(len(Extended.objects.all())==0, len(Extended.objects.all()))
        self.assert_(len(ChildA.objects.all())==0, len(ChildA.objects.all()))
        self.assert_(len(ChildB.objects.all())==0, len(ChildB.objects.all()))
        form = self.klass({'_selected_child':'ChildA', 'a':5, 'childa_b':6})
        form.save()
        self.assert_(len(Extended.objects.all())==1, len(Extended.objects.all()))
        self.assert_(len(ChildA.objects.all())==1, len(ChildA.objects.all()))
        self.assert_(len(ChildB.objects.all())==0, len(ChildB.objects.all()))
        parent = Extended.objects.all()[0]
        child = ChildA.objects.all()[0]
        self.assert_(parent.a==5, parent.a)
        self.assert_(child.a==5, child.a)
        self.assert_(child.b==6, child.b)

    def test_update_child(self):
        self.assert_(len(Extended.objects.all())==0, len(Extended.objects.all()))
        self.assert_(len(ChildA.objects.all())==0, len(ChildA.objects.all()))
        self.assert_(len(ChildB.objects.all())==0, len(ChildB.objects.all()))
        child = ChildA()
        child.id = 1
        child.a = 5
        child.b = 6
        child.save()
        form = self.klass({'_selected_child':'ChildA', 'pk':1, 'childa_id':1, 'a':7, 'childa_b':8})
        form.save()
        self.assert_(len(Extended.objects.all())==1, len(Extended.objects.all()))
        self.assert_(len(ChildA.objects.all())==1, len(ChildA.objects.all()))
        self.assert_(len(ChildB.objects.all())==0, len(ChildB.objects.all()))
        parent = Extended.objects.all()[0]
        child = ChildA.objects.all()[0]
        self.assert_(parent.a==7, parent.a)
        self.assert_(child.a==7, child.a)
        self.assert_(child.b==8, child.b)

    def test_update_parent(self):
        self.assert_(len(Extended.objects.all())==0, len(Extended.objects.all()))
        self.assert_(len(ChildA.objects.all())==0, len(ChildA.objects.all()))
        self.assert_(len(ChildB.objects.all())==0, len(ChildB.objects.all()))
        parent = Extended()
        parent.id = 1
        parent.a = 4
        parent.save()
        form = self.klass({'_selected_child':'', 'pk':1, 'a':5})
        form.save()
        self.assert_(len(Extended.objects.all())==1, len(Extended.objects.all()))
        self.assert_(len(ChildA.objects.all())==0, len(ChildA.objects.all()))
        self.assert_(len(ChildB.objects.all())==0, len(ChildB.objects.all()))
        parent = Extended.objects.all()[0]
        self.assert_(parent.a==5, parent.a)
    
    def test_permissions(self):
        pass
    

class Form_Parent_Depth_Test(unittest.TestCase):
    """
    Tests for a parent class that has children who also have children
    """

    def setUp(self):
        root = RootPluginManager()
        config = PluginConfig()
        manager = ModelManager(root, config)
        parent = ModelWrapper(ExtendedDepthTest)
        child1 = ModelWrapper(ChildLevel1)
        child2 = ModelWrapper(ChildLevel2)
        manager.register(parent)
        manager.register(child1)
        manager.register(child2)
        view = ModelEditView(parent)
        self.klass = view.get_form()
        self.attrs = view.get_fields(parent)

    def test_form_structure(self):
        dict = self.attrs
        form = self.klass.form
        # field contents
        self.assert_(issubclass(form,(ParentBase,)), form)
        self.assert_(len(form.children)==2,form.children)
        self.assert_('ChildLevel1' in form.children, form.children)
        self.assert_('ChildLevel2' in form.children, form.children)
        self.assert_(len(form.recurse)==1, form.recurse)
        self.assert_('a' in dict, dict)

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
        self.attrs = view.get_fields(child)
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

    def setUp(self):
        root = RootPluginManager()
        config = PluginConfig()
        self.manager = ModelManager(root, config)
        parent = ModelWrapper(Complex)
        child = ModelWrapper(OneToMany)
        self.manager.register(parent)
        self.manager.register(child)
        view = ModelEditView(parent)
        self.attrs = view._get_form()
        self.klass = view.get_form()

    def tearDown(self):
        Complex.objects.all().delete()
        OneToMany.objects.all().delete()

    def test_form_structure(self):
        """
        Tests:
            * OneToMany is added as a BaseField
            * OneToMany Form has the correct fields in its attrs
        """
        dict = self.attrs
        self.assert_('one_to_manys' in dict['one_to_many'], dict['one_to_many'])
        self.assert_(len(dict['one_to_many']), dict['one_to_many'])
        subklass = dict['one_to_many'].values()[0]
        self.assert_(issubclass(subklass, Related1ToMBase), subklass)
        attrs = subklass.attrs
        self.assert_(len(attrs)==2, attrs)
        self.assert_('one_to_manys_b' in attrs, attrs)
        self.assert_('one_to_manys_complex' in attrs, attrs)

    def test_load(self):
        """
        Tests creating instances of the form with initial data
        """
        data = {
            'id':1,
            'one_to_manys_count':1,
            'one_to_manys_complex_1':1,
            'one_to_many_b_1':2
        }
        i = self.klass(data)
        self.assert_(len(i.one_to_many_instances)==1, i.one_to_many_instances)
        i = i.one_to_many_instances.values()[0]
        self.assert_(len(i.instances)==2, i.instances)
    
    def test_instantiate(self):
        """
        Tests creating an unbound copy of the form
        """
        pass
    
    def test_create(self):
        pass
    
    def test_save(self):
        pass
    
    def test_permissions(self):
        pass


class Form_Many_To_One_Test(unittest.TestCase):

    def setUp(self):
        root = RootPluginManager()
        config = PluginConfig()
        manager = ModelManager(root, config)
        parent= ModelWrapper(Complex)
        manager.register(parent)
        child= ModelWrapper(OneToMany)
        manager.register(child)
        view = ModelEditView(child)
        self.attrs = view.get_fields(child)
        self.klass = view.get_form()

    def tearDown(self):
        OneToMany.objects.all().delete()
        Complex.objects.all().delete()

    def test_form_structure(self):
        dict = self.attrs
        # field contents
        self.assert_('complex' in dict, dict)
        self.assert_(issubclass(dict['complex'].__class__, (forms.ModelChoiceField,)), dict)

    def test_save(self):
        self.assert_(len(Complex.objects.all())==0, len(Complex.objects.all()))
        self.assert_(len(OneToMany.objects.all())==0, len(OneToMany.objects.all()))
        parent = Complex()
        parent.id = 1
        parent.save()
        data = {
            'b':3,
            'complex':1
        }
        form = self.klass(data)
        form.save()
        parent = Complex.objects.all()[0]
        self.assert_(len(parent.one_to_manys.all())==1, parent.one_to_manys.all())
        child = parent.one_to_manys.all()[0]
        self.assert_(child.b==3, child.b)
    
    def test_permissions(self):
        pass
    
    
class Form_Many_To_Many_Test(unittest.TestCase):

    def setUp(self):
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