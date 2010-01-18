from django import forms
from core.plugins import Plugin


class FooConfig(forms.Form):
    number = forms.IntegerField(initial='0', help_text='This is a number field')
    string = forms.CharField(initial='abc123', help_text='This is a string field')
    select = forms.ChoiceField(initial='b', choices=(('a','a'),('b','b'),('c','c')))

class Foo(Plugin):
    """test plugin"""
    config_form = FooConfig
    
class Bar(Plugin):
    """test plugin"""
    depends = (Foo)
    