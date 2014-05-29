from os.path import abspath, dirname, join

DEFAULT_INSTALL_PATH = '/opt/ganeti_webmgr'

# Path Helpers
def install_path(*x):
    """
    A wrapper around join which will return a path relative to the
    default install path.
    """
    return join(DEFAULT_INSTALL_PATH, *x)

DEFAULT_CONFIG_PATH = install_path('config', 'config.yml')

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

