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
        # Make sure ganeti_webmgr settings are being used.
        #  This ensures installed apps are properly imported.
        if not os.environ.has_key('DJANGO_SETTINGS_MODULE'):
            os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

        from ganeti_web.cache.service import CacheService
        return CacheService()


servicemaker = CacheUpdaterServiceMaker()
