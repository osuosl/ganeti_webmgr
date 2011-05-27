import sys
import os

# ==========================================================
# Setup django environment
# ==========================================================
if not os.environ.has_key('DJANGO_SETTINGS_MODULE'):
    sys.path.insert(0, os.getcwd())
    from django.core.management import setup_environ
    import settings
    setup_environ(settings)

from twisted.application import service
from ganeti.cache.service import CacheService

application = service.Application("Ganeti Web Manager Cache Updater")
service = CacheService()
service.setServiceParent(application)