# This is imported as the DJANGO_SETTINGS_MODULE.
# First it trys to import settings.py which should import base.py

# Returns a hopefully more useful error message if someone forgets to
# rename settings.py.dist to settings.py
import sys

try:
    from .settings import *
except ImportError:
    msg = "Did you rename settings/settings.py.dist to settings/settings.py?)"
    print >> sys.stderr, msg
