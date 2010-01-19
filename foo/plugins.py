from django import forms
from core.plugins import Plugin

from core.tests.test_plugins import *

class FooConfig(forms.Form):
    number = forms.IntegerField(initial='0', help_text='This is a number field')
    string = forms.CharField(initial='abc123', help_text='This is a string field')
    select = forms.ChoiceField(initial='b', choices=(('a','a'),('b','b'),('c','c')))
    
class Foo(Plugin):
    """test plugin"""
    config_form = FooConfig


class BarConfigA(forms.Form):
    number = forms.IntegerField(initial='0', help_text='This is a number field')
    string = forms.CharField(initial='abc123', help_text='This is a string field')
    select = forms.ChoiceField(initial='b', choices=(('a','a'),('b','b'),('c','c')))

class BarConfigB(forms.Form):
    name = 'Other'
    number2 = forms.IntegerField(initial='0', help_text='This is a number field')
    string2 = forms.CharField(initial='abc123', help_text='This is a string field')
    select2 = forms.ChoiceField(initial='b', choices=(('a','a'),('b','b'),('c','c')))
    
class Bar(Plugin):    
    config_form = (BarConfigA, BarConfigB)
    
    """test plugin"""
    depends = (Foo)
    