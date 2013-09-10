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

These settings are hopefully so universal that they never need to change
between deployments and are factored out into this module to avoid stale
end_user.py files causing upgrade bugs.

All settings in this module can be overriden in the main end_user.py module,
of course.
"""
from os.path import abspath, basename, dirname, join
from sys import path

##### Project structure variables #####
PROJECT_ROOT = dirname(dirname(abspath(__file__)))
DOC_ROOT = dirname(PROJECT_ROOT)
SITE_NAME = basename(PROJECT_ROOT)

# Add our project to our pythonpath
path.append(PROJECT_ROOT)

##### Debug *default* configuration #####
DEBUG = False
TEMPLATE_DEBUG = DEBUG
##### End Debug configuration #####

##### General Defaults #####
SITE_ID = 1
LOGIN_REDIRECT_URL = '/'

USE_I18N = True
USE_L10N = True
##### End General defaults #####


##### Items per page defaults #####
# default max number of disks that can be added at once to an instance
MAX_DISKS_ADD = 8
# default max number of NICS that can be added at once to an instance
MAX_NICS_ADD = 8
# default items per page
ITEMS_PER_PAGE = 15
##### End Items per page defaults #####

##### Haystack settings #####
HAYSTACK_SITECONF = 'search_sites'
HAYSTACK_SEARCH_ENGINE = 'whoosh'
HAYSTACK_WHOOSH_PATH = join(PROJECT_ROOT, 'whoosh_index')
##### End Haystack settings #####


###### Template Configuration #####
TEMPLATE_DIRS = (
    join(DOC_ROOT, 'templates')
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
    'ganeti_web.context_processors.site',
    'ganeti_web.context_processors.common_permissions',
)
###### End Template Configuration #####

###### Static Files Configuration #####
STATIC_URL = '/static'

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

STATICFILES_DIRS = (
    join(DOC_ROOT, 'static'),
)

STATIC_ROOT = join(DOC_ROOT, "collected_static")
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
    'ganeti_web.middleware.PermissionDeniedMiddleware'
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
    'ganeti_web',
    'object_permissions',
    'object_log',
    'south',
    'haystack',
    'muddle',
    'muddle.shots',
    'muddle_users',


    # ganeti apps
    'authentication',
    'clusters',
    'jobs',
    'nodes',
    'utils',
    'virtualmachines',
    'vm_templates',
    'ganetiviz',
)

ROOT_URLCONF = 'ganeti_web.urls'
AUTH_PROFILE_MODULE = 'authentication.Profile'


# Horrible Django hack for convincing Django that we are i18n'd.
def ugettext(s):
    return s

# Ganeti Cached Cluster Objects Timeouts
#    LAZY_CACHE_REFRESH (milliseconds) is the fallback cache timer that is
#    checked when the object is instantiated. It defaults to 600000ms, or ten
#    minutes.
LAZY_CACHE_REFRESH = 600000
# Other GWM Stuff
VNC_PROXY = 'localhost:8888'
RAPI_CONNECT_TIMEOUT = 3
WEB_MGR_API_KEY = "CHANGE_ME"
