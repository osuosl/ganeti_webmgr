import sys
import os

from twisted.application.service import IServiceMaker
from twisted.plugin import IPlugin
from twisted.python.usage import Options
from zope.interface import implements

class CacheUpdaterOptions(Options):
    optParameters = [
    ]

    
class CacheUpdaterServiceMaker(object):

    implements(IPlugin, IServiceMaker)

    tapname = "gwm_cache"
    description = "Ganeti Web Manager cache updater"
    options = CacheUpdaterOptions

    def makeService(self, options):
        """
        Setup django environment and start cache service
        """
        if not os.environ.has_key('DJANGO_SETTINGS_MODULE'):
            sys.path.insert(0, os.getcwd())
            from django.core.management import setup_environ
            import settings
            setup_environ(settings)

        from ganeti.cache.service import CacheService
        return CacheService()


servicemaker = CacheUpdaterServiceMaker()