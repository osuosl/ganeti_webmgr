from ganeti_webmgr.muddle.tests.apps.load_app_plugin.test_plugin import TestPlugin


class TestPluginFoo(TestPlugin):
    pass


class TestPluginBar(TestPlugin):
    pass


class NotAPlugin(object):
    pass


class NotAPluginEither(NotAPlugin):
    pass


AN_INTEGER = 1
A_STRING = 'abc'

