from core.plugins import Plugin

class Foo(Plugin):
    """test plugin"""
    pass
    
class Bar(Plugin):
    """test plugin"""
    depends = (Foo)
    