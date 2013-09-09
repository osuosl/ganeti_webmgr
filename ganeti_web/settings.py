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
settings.py files causing upgrade bugs.

All settings in this module can be overriden in the main settings.py module,
of course.
"""

__all__ = (
    "AUTH_PROFILE_MODULE",
    "INSTALLED_APPS",
    "MIDDLEWARE_CLASSES",
    "TEMPLATE_CONTEXT_PROCESSORS",
    "TEMPLATE_LOADERS",
    "ugettext",
)


# Horrible Django hack for convincing Django that we are i18n'd.
def ugettext(s):
    return s

# List of callables that know how to import templates from various sources.
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
    'ganeti_web.middleware.PermissionDeniedMiddleware',
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
    'include_strip_tag',
    'django_tables2',
)

# The model that contains extra user profile stuff.
AUTH_PROFILE_MODULE = 'ganeti_web.Profile'
