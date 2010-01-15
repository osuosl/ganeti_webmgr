from maintain.core.modules import Plugin

class PluginNoDepends(Plugin):
    """plugin with no dependencies"""
    pass

class PluginNoDependsB(Plugin):
    """another plugin with no dependencies"""
    pass

class PluginOneDepends(Plugin):
    """Plugin with a single dependency"""
    depends = (PluginNoDepends)
    
class PluginOneDependsB(Plugin):
    """Plugin with a single dependency"""
    depends = (PluginNoDepends)

class PluginTwoDepends(Plugin):
    """Plugin with two dependencies"""
    depends = (PluginNoDepends, PluginNoDependsB)
    
class PluginRecursiveDepends(Plugin):
    """plugin with recursive dependency"""
    depends = (PluginOneDepends)
    
class PluginRedundantRecursiveDepends(Plugin):
    """Plugin with recursive dependency that is recursive"""
    depends = (PluginOneDepends, PluginNoDepends)

class PluginRedundentDepends(Plugin):
    """Plugin with redundant dependencies"""
    depends = (PluginNoDepends, PluginNoDepends)
    
class PluginH(Plugin):
    depends = (PluginOneDepends, PluginRecursiveDepends, PluginNoDepends)

class PluginCycleA(Plugin):
    """I am part of an cyclic error"""
    pass
    
class PluginCycleB(Plugin):
    """I am part of an cyclic error"""
    depends = (PluginCycleA)
PluginCycleA.depends = (PluginCycleB)

class PluginIndirectCycleA(Plugin):
    """I am part of an indirect cyclic error"""
    pass
    
class PluginIndirectCycleB(Plugin):
    """I am part of an indirect cyclic error"""
    depends = (PluginIndirectCycleA)

class PluginIndirectCycleC(Plugin):
    """I am part of an indirect cyclic error"""
    depends = (PluginIndirectCycleB)
PluginIndirectCycleA.depends = (PluginIndirectCycleC)

class PluginFailsWhenEnabled(Plugin):
    """I fail when you try to create an instance of me.  Used for testing
    enable/disabling of tasks"""
    def __init__(self):
        0/0+FAKE

class PluginFailingDepends(Plugin):
    """I have one dependency that fails, should not trigger rollback"""
    depends = (PluginFailsWhenEnabled)
    
class PluginFailsWithDepends(PluginFailsWhenEnabled):
    """I Fail myself, but i have dependency that will be loaded before me.  used
    for testing enabling that will result in a rollback of changes"""
    depends = (PluginNoDepends)
    
class PluginDependsFailsRequiresRollback(PluginFailsWhenEnabled):
    """I have a dependency that will fail, but only after its recursive depend
    as been enabled.  I require a rollback"""
    depends = (PluginNoDepends, PluginNoDependsB, PluginFailsWhenEnabled)
