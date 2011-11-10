import os

import pkg_resources

from fabric.api import env
from fabric.context_managers import settings, hide, lcd
from fabric.contrib.files import exists
from fabric.operations import local, require, prompt

# Required dependencies
#
#    PIP_INSTALL - install packages from pip:  name:version
#
#    GIT_INSTALL - install packages from git:
#
#                    url - git url for checkouts
#                    development - head to checkout for dev.  Defaults to master
#                    production - head to checkout for prod.  defaults to master.
#                    symlink - directory to symlink into project.  uses project
#                              name if blank
# Packages from git are given preference for dev environment. PIP is given
# preference for production environments

PIP_INSTALL = dict((r.project_name, str(r)) for r in
                   pkg_resources.parse_requirements(open("requirements.txt").read()))

GIT_INSTALL =  {
    'ganeti_webmgr_layout':{
        'url':'git://git.osuosl.org/gitolite/ganeti/ganeti_webmgr_layout',
        'development':'develop',
        'symlink':'ganeti_web_layout',
        },
    'noVNC':{
        'url':'git://github.com/kanaka/noVNC.git',
        'development':'3859e1d35cf',
        'production':'3859e1d35cf',
        },
    'django_object_permissions':{
        'url':'git://git.osuosl.org/gitolite/django/django_object_permissions',
        'development':'develop',
        },
    'django_object_log':{
        'url':'git://git.osuosl.org/gitolite/django/django_object_log',
        'development':'develop',
        },
    'django_muddle_users':{
        'url':'git://git.osuosl.org/gitolite/django/django_muddle_users',
        'development':'develop',
        },
    'muddle':{
        'url':'git://git.osuosl.org/gitolite/django/muddle',
        'development':'develop',
        },
    'twisted_vncauthproxy':{
        'url':'git://git.osuosl.org/gitolite/ganeti/twisted_vncauthproxy',
        'development':'develop',
    },
    'django-tastypie':{
        'url':'https://github.com/toastdriven/django-tastypie.git',
        'development':'master',
    }
}


# default environment settings - override these in environment methods if you
# wish to have an environment that functions differently
env.doc_root = '.'
env.remote = False


def dev():
    """
    Configure development deployment.
    """

    env.environment = 'development'


def prod():
    """
    Configure production deployment.
    """

    env.environment = 'production'


# Files and directories that will be included in tarball when packaged
env.MANIFEST = [
    "django_test_tools",
    "deprecated",
    "ganeti_web",
    #"i18n",
    "locale",
    "media",
    "templates",
    "twisted",
    "util",
    "__init__.py",
    "AUTHORS",
    "CHANGELOG",
    "COPYING",
    "fabfile.py",
    "LICENSE",
    "manage.py",
    "README",
    "search_sites.py",
    "settings.py.dist",
    "UPGRADING",
    "urls.py",
    "requirements.txt",
]


def deploy():
    """
    Install all dependencies from git and pip.
    """

    install_dependencies_pip()
    install_dependencies_git()


def _exists(path):
    """
    A helper function to determine whether a path exists.

    This function does the right thing in both remote and local environments.
    """

    if env.remote:
        return exists(path)
    else:
        return os.path.exists(path)


def create_virtualenv(virtualenv=None, force=False):
    """
    Create a virtualenv for pip installations.

    By default, the environment will be placed in the document root. Pass a
    path to override the location.

    If ``force`` is False, then the environment will not be recreated if it
    already exists.
    """

    require('environment', provided_by=[dev, prod])
    env.virtualenv = virtualenv if virtualenv else env.doc_root

    with lcd(env.doc_root):
        if not force and _exists('%(virtualenv)s/lib' % env):
            print 'virtualenv already created'
        else:
            # XXX does this actually create a new environment if one already
            # exists there?
            local('virtualenv %(virtualenv)s' % env)


def create_env():
    """
    Setup environment for git dependencies.
    """

    require('environment', provided_by=[dev, prod])

    with lcd(env.doc_root):
        if _exists('dependencies'):
            print 'dependencies directory exists already'
        else:
            local('mkdir dependencies')


def install_dependencies_pip():
    """
    Install all dependencies available from pip.
    """

    require('environment', provided_by=[dev, prod])
    create_virtualenv()

    # if this is a development install then filter out anything we have a
    # git repo for.
    pips_ = PIP_INSTALL.copy()
    if env.environment == 'development':
        map(pips_.pop, [k for k in GIT_INSTALL if k in PIP_INSTALL])

    if not pips_:
        print 'No git repos to install'
        return

    with lcd(env.doc_root):
        # Run the installation with pip, passing in our requirements.txt.
        local('pip install -E %(virtualenv)s -r requirements.txt' % env)


def install_dependencies_git():
    """
    Install all dependencies available from git.
    """

    require('environment', provided_by=[dev, prod])

    # if this is a production install then install everything that pip that
    # can be installed
    gits_ = GIT_INSTALL.copy()
    if env.environment != 'development':
        map(gits_.pop, (k for k in PIP_INSTALL if k in GIT_INSTALL))

    if not gits_:
        print 'No git repos to install'
        return

    create_env()

    for name, opts in GIT_INSTALL.items():

        # check for required values
        if 'url' not in opts:
            raise Exception('missing required argument "url" for git repo: %s' % name)

        # set git head to check out
        if env.environment in opts:
            opts['head'] = opts[env.environment]
        elif env.environment == 'development' and 'production' in opts:
            opts['head'] = opts['production']
        else:
            opts['head'] = 'master'

        # clone repo
        with lcd('%(doc_root)s/dependencies' % env):
            env.git_repo = name
            if not _exists('%(doc_root)s/dependencies/%(git_repo)s' % env):
                local('git clone %(url)s' % opts)

            # create branch if not using master
            if opts['head'] != 'master':
                with lcd(name):
                    local('git fetch')
                    local('git checkout %(head)s' % opts)
                    with settings(hide('warnings','stderr'), warn_only=True):
                            local('git pull')

        # install to virtualenv using setup.py if it exists.  Some repos might
        # not have it and will need to be symlinked into the project
        if _exists('%(doc_root)s/dependencies/%(git_repo)s/setup.py' % env):
            with lcd(env.doc_root):
                local('pip install -E %(virtualenv)s -e dependencies/%(git_repo)s' % env)

        else:
            # else, configure and create symlink to git repo
            with lcd (env.doc_root):
                if 'symlink' in opts:
                    env.symlink = opts['symlink']
                    env.symlink_path = '%(doc_root)s/dependencies/%(git_repo)s/%(symlink)s' % env
                else:
                    env.symlink = name
                    env.symlink_path = '%(doc_root)s/dependencies/%(git_repo)s' % env

                with settings(hide('warnings','stderr'), warn_only=True):
                    local('ln -sf %(symlink_path)s %(doc_root)s' % env)



def tarball():
    """
    Package a release tarball.
    """

    tarball = prompt('tarball name', default='ganeti-webmgr-tar.gz')
    files = ['ganeti_webmgr/%s' % file for file in env.MANIFEST]
    files = ' '.join(files)

    with lcd('..'):
        data = dict(
            tarball=tarball,
            files=files
        )
        local('tar cfz %(tarball)s %(files)s --exclude=*.pyc' % data)
        local('mv %(tarball)s ./ganeti_webmgr/' % data)
