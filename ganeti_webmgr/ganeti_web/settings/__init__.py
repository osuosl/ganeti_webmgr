# This module is how we import settings, and override settings with various
# precedences.

# First our base.py settings module is imported, with all of the
# important defaults.
#
# Next our yaml file is opened, read, and settings defined in the yaml config
# may override settings already defined.
#
# Lastly, settings.py is imported if it exists, and it can override settings
# as well.

from .base import *
from .yaml_config import *

try:
    from .settings import *
except ImportError:
    pass

try:
    from .ldap_settings import *
except ImportError:
    pass
