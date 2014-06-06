# Copyright (C) 2012 Oregon State University
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.

"""
Default settings for GWM.

Most of this should be left alone and unchanged.
"""

from os import makedirs
from os.path import exists, join
from .helpers import (
    app_root, CONFIG_PATH, DEFAULT_INSTALL_PATH,
    generate_secret, ugettext
)

##### Debug *default* configuration #####
DEBUG = False
TEMPLATE_DEBUG = DEBUG
TESTING = False
##### End Debug configuration #####

##### General Defaults #####
SITE_ID = 1
LOGIN_REDIRECT_URL = '/'
SITE_NAME = 'Ganeti Web Manager'
SITE_DOMAIN = 'localhost:8000'
SITE_ROOT = ''

USE_I18N = True
USE_L10N = True
##### End General defaults #####

##### Registration Settings #####
ACCOUNT_ACTIVATION_DAYS = 7
##### End Registration Settings #####

##### Items per page defaults #####
# default max number of disks that can be added at once to an instance
MAX_DISKS_ADD = 8
# default max number of NICS that can be added at once to an instance
MAX_NICS_ADD = 8
# default items per page
ITEMS_PER_PAGE = 15
##### End Items per page defaults #####

##### Haystack settings #####
HAYSTACK_SITECONF = 'ganeti_webmgr.search_sites'
HAYSTACK_SEARCH_ENGINE = 'whoosh'
HAYSTACK_WHOOSH_PATH = join(DEFAULT_INSTALL_PATH, 'whoosh_index')
##### End Haystack settings #####


###### Template Configuration #####
TEMPLATE_DIRS = (
    app_root('templates')
)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.contrib.messages.context_processors.messages',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.request',
    'django.core.context_processors.static',
    'ganeti_webmgr.ganeti_web.context_processors.site',
    'ganeti_webmgr.ganeti_web.context_processors.common_permissions',
)
###### End Template Configuration #####

###### Static Files Configuration #####
STATIC_URL = '/static'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

STATICFILES_DIRS = (
    app_root('static'),
)

STATIC_ROOT = join(DEFAULT_INSTALL_PATH, "collected_static")
###### End Static Files Configuration #####

###### Other Configuration #####
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'object_permissions.backend.ObjectPermBackend',
)

##### Logging Configuration #####
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
##### End Logging Configuration #####

# Middleware. Order matters; these are all applied *in the order given*.
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    # Transaction middleware is early so that it can apply to all later
    # middlewares.
    'django.middleware.transaction.TransactionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'ganeti_webmgr.ganeti_web.middleware.PermissionDeniedMiddleware'
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    "django.contrib.formtools",
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'registration',
    'include_strip_tag',
    'django_tables2',
    # ganeti_web must come before object_permissions in order to migrate from
    # 0.7 or older successfully.
    'ganeti_webmgr.ganeti_web',
    'object_permissions',
    'object_log',
    'south',
    'haystack',
    'ganeti_webmgr.muddle',
    'ganeti_webmgr.muddle.shots',
    'ganeti_webmgr.muddle_users',

    # ganeti apps
    'ganeti_webmgr.authentication',
    'ganeti_webmgr.clusters',
    'ganeti_webmgr.jobs',
    'ganeti_webmgr.nodes',
    'ganeti_webmgr.utils',
    'ganeti_webmgr.virtualmachines',
    'ganeti_webmgr.vm_templates',
    'ganeti_webmgr.ganetiviz',
)

ROOT_URLCONF = 'ganeti_webmgr.ganeti_web.urls'
AUTH_PROFILE_MODULE = 'authentication.Profile'

##### Locale Configuration #####
LOCALE_PATHS = (
    app_root("locale"),
)

LANGUAGES = (
    ('el', ugettext('Greek')),
    ('en', ugettext('English')),
)

# Ganeti Cached Cluster Objects Timeouts
#    LAZY_CACHE_REFRESH (milliseconds) is the fallback cache timer that is
#    checked when the object is instantiated. It defaults to 600000ms, or ten
#    minutes.
LAZY_CACHE_REFRESH = 600000
# Other GWM Stuff
VNC_PROXY = 'localhost:8888'
RAPI_CONNECT_TIMEOUT = 3


def create_secrets(folder='.secrets'):
    # Generate a secret key, and store it in a file to be read later.
    secrets_folder = join(DEFAULT_INSTALL_PATH, folder)

    # Directory doesn't exist, create it
    if not exists(secrets_folder):
        try:
            makedirs(secrets_folder)
        except (IOError, OSError):
            print ('Unable to create directory, at %s. Please make sure to set the '
                   'SECRET_KEY and WEB_MGR_API_KEY setting in config.yml'
                   % secrets_folder)
            return

    secret_key_file = join(secrets_folder, 'SECRET_KEY.txt')
    api_key_file = join(secrets_folder, 'WEB_MGR_API_KEY.txt')
    secret_key_file_exists = exists(secret_key_file)
    api_key_file_exists = exists(api_key_file)
    try:
        # File containing secretkey doesnt exist, so create it and fill it with the key
        if not secret_key_file_exists:
            with open(secret_key_file, "w") as f:
                SECRET_KEY = generate_secret()
                f.write(SECRET_KEY)
        # File does exist, open it and read the value from it
        else:
            with open(secret_key_file, "r") as f:
                SECRET_KEY = f.read().strip()

        # do the same as above for the WEB_MGR_API_KEY
        if not api_key_file_exists:
            with open(api_key_file, "w") as f:
                WEB_MGR_API_KEY = generate_secret()
                f.write(WEB_MGR_API_KEY)
        # File does exist, open it and read the value from it
        else:
            with open(api_key_file, "r") as f:
                WEB_MGR_API_KEY = f.read().strip()

    except (IOError, OSError):
        action = 'create' if secret_key_file_exists else 'open'
        msg = ("Unable to %s file at %s. Please either create the file and ensure "
               "it contains a 32bit random value or ensure you have set the "
               "SECRET_KEY setting in %s.")
        print msg % (action, secret_key_file, CONFIG_PATH)

create_secrets()