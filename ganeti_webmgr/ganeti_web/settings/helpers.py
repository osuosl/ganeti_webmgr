import os
from os.path import abspath, dirname, join

# This is simply a default location we've decided that some configuration
# settings will use for their path.
#
# Making it configurable doesn't make a lot of sense because this is only where
# default settings put files, such as static assets, the whoosh index, ect.
# All of which can be configured in the yaml config file anyways.
DEFAULT_INSTALL_PATH = '/opt/ganeti_webmgr'

# Config location variables

# default config directory is DEFAULT_INSTALL_PATH/config
DEFAULT_CONFIG_DIR = join(DEFAULT_INSTALL_PATH, 'config')
# try getting config directory from environment,
# defaulting to DEFAULT_CONFIG_DIR
CONFIG_DIR = os.environ.get('GWM_CONFIG_DIR', DEFAULT_CONFIG_DIR)
# our config file is always named config.yml
CONFIG_PATH = join(CONFIG_DIR, 'config.yml')


# Path Helpers
def here(*x):
    """
    This is a wrapper around join. It will return a path relative to the
    current file.
    """
    return join(abspath(dirname(__file__)), *x)

# This is the directory containing our python package
# This will be site-packages or the root of the git checkout if not installed
# as a python package
PROJECT_ROOT = here("..", "..", "..")

def root(*x):
    """
    This is a wrapper around join. It will return a path relative to
    PROJECT_ROOT.
    """
    return join(abspath(PROJECT_ROOT), *x)

app_root = lambda *x: root('ganeti_webmgr', *x)

##### Project structure variables #####
SITE_NAME = 'Ganeti Web Manager'

def generate_secret(secret_size=32):
    "Generates a secret key of the given size"
    import random
    import string
    valid_chars = string.digits + string.letters
    return ''.join(
        random.SystemRandom().choice(valid_chars)
        for i in xrange(secret_size)
    )

def ugettext(s):
    """Horrible Django hack for convincing Django that we are i18n'd."""
    return s

