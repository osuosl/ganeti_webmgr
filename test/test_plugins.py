from django import forms
from muddle.plugins.plugin import Plugin

class PluginNoDepends(Plugin):
    """plugin with no dependencies"""
    description = "I am a plugin with no dependencies"

class PluginNoDependsB(Plugin):
    """another plugin with no dependencies"""
    description = "I am another plugin with no dependencies"

class PluginOneDepends(Plugin):
    """Plugin with a single dependency"""
    description = "I am a plugin with a single dependency on PluginNoDepends"
    depends = (PluginNoDepends)
    
class PluginOneDependsB(Plugin):
    """Plugin with a single dependency"""
    description = "I am another plugin with a single dependency on PluginNoDepends"
    depends = (PluginNoDepends)

class PluginTwoDepends(Plugin):
    """Plugin with two dependencies"""
    description = "I am a plugin with two dependencies:  PluginNoDepends and PluginNoDependsB"
    depends = (PluginNoDepends, PluginNoDependsB)
    
class PluginRecursiveDepends(Plugin):
    """plugin with recursive dependency"""
    description = "I am a plugin with a recursive dependency.  I depend on " + \
                  "PluginOneDepends, which depends on PluginNoDepends.  As " + \
                  "a result I also depend on PluginOneDepends"
    depends = (PluginOneDepends)
    
class PluginRedundantRecursiveDepends(Plugin):
    """Plugin with recursive dependency that is recursive"""
    description = "I am a plugin with a recursive dependency.  I depend on " + \
                  "PluginNoDepends both directly and indirectly through " + \
                  "PluginOneDepends"
    depends = (PluginOneDepends, PluginNoDepends)

class PluginRedundentDepends(Plugin):
    """Plugin with redundant dependencies"""
    description = "I depend on PluginNoDepends, twice."
    depends = (PluginNoDepends, PluginNoDepends)
    
class PluginH(Plugin):
    description = "I was thought usefull at one point, but i can't remember what I'm for"
    depends = (PluginOneDepends, PluginRecursiveDepends, PluginNoDepends)

class PluginCycleA(Plugin):
    """I am part of an cyclic error"""
    description = "I am part of a direct dependency cycle with PluginCycleB"
    
class PluginCycleB(Plugin):
    """I am part of an cyclic error"""
    description = "I am part of a direct dependency cycle with PluginCycleB"
    depends = (PluginCycleA)
PluginCycleA.depends = (PluginCycleB)

class PluginIndirectCycleA(Plugin):
    """I am part of an indirect cyclic error"""
    description = "I am part of a indirect dependency cycle with " + \
                  "PluginIndirectCycleB and PluginIndirectCycleC"
    
class PluginIndirectCycleB(Plugin):
    """I am part of an indirect cyclic error"""
    depends = (PluginIndirectCycleA)
    description = "I am part of a indirect dependency cycle with " + \
                  "PluginIndirectCycleA and PluginIndirectCycleC"

class PluginIndirectCycleC(Plugin):
    """I am part of an indirect cyclic error"""
    depends = (PluginIndirectCycleB)
    description = "I am part of a indirect dependency cycle with " + \
                  "PluginIndirectCycleA and PluginIndirectCycleB"
PluginIndirectCycleA.depends = (PluginIndirectCycleC)

class PluginFailsWhenEnabled(Plugin):
    """I fail when you try to create an instance of me.  Used for testing
    enable/disabling of tasks"""
    description = "I throw an exception when initialized"
    def __init__(self, manager, plugin_config):
        0/0+FAKE

class PluginFailingDepends(Plugin):
    """I have one dependency that fails, should not trigger rollback"""
    description = "I have a dependency that throws an exception when initialized"
    depends = (PluginFailsWhenEnabled)
    
class PluginFailsWithDepends(PluginFailsWhenEnabled):
    """I Fail myself, but i have dependency that will be loaded before me.  used
    for testing enabling that will result in a rollback of changes"""
    description = "I fail when enabled and have a dependency.  When enabling "+\
                  "me my depends will be enabled first.  It will need to be " +\
                  "disabled again if it were not already enabled"
    depends = (PluginNoDepends)
    
class PluginDependsFailsRequiresRollback(PluginFailsWhenEnabled):
    """I have a dependency that will fail, but only after its recursive depend
    as been enabled.  I require a rollback"""
    depends = (PluginNoDepends, PluginNoDependsB, PluginFailsWhenEnabled)
    description = "I fail when enabled and have several dependencies, one of "+\
                  "which will fail When enabled.  I am used for testing " + \
                  "rollbacks and partial rollbacks when one plugin was " +\
                  "enabled prior to attempting to enable me"

class Config(forms.Form):
    number = forms.IntegerField(initial='0', help_text='This is a number field')
    string = forms.CharField(initial='abc123', help_text='This is a string field')
    select = forms.ChoiceField(initial='b', choices=(('a','a'),('b','b'),('c','c')))
    
class PluginWithConfig(Plugin):
    """test plugin"""
    description = "I am a plugin with a configuration form"
    config_form = Config


class ConfigA(forms.Form):
    number = forms.IntegerField(initial='0', help_text='This is a number field')
    string = forms.CharField(initial='abc123', help_text='This is a string field')
    select = forms.ChoiceField(initial='b', choices=(('a','a'),('b','b'),('c','c')))

class ConfigB(forms.Form):
    name = 'Other'
    number2 = forms.IntegerField(initial='0', help_text='This is a number field')
    string2 = forms.CharField(initial='abc123', help_text='This is a string field')
    select2 = forms.ChoiceField(initial='b', choices=(('a','a'),('b','b'),('c','c')))
    
class PluginWithTabbedConfig(Plugin):
    description = "I am a plugin with two configuration forms.  The forms " + \
                  "are displayed as tabs when edited"
    config_form = (ConfigA, ConfigB)
    depends = (PluginWithConfig)
