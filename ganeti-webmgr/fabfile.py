import os

import pkg_resources

from fabric.api import env, abort
from fabric.context_managers import settings, hide, lcd
from fabric.contrib.console import confirm
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
    'django_object_permissions':{
        'url':'git://git.osuosl.org/gitolite/django/django_object_permissions',
        'development':'develop',
        },
    'django_object_log':{
        'url':'git://git.osuosl.org/gitolite/django/django_object_log',
        'development':'develop',
        },
    'twisted_vncauthproxy':{
        'url':'git://git.osuosl.org/gitolite/ganeti/twisted_vncauthproxy',
        'development':'develop',
    },
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


# List of stuff to include in the tarball, recursive.
env.MANIFEST = [
    # Directories
    "deprecated",
    "django_test_tools",
    "ganeti_web",
    "locale",
    # Files
    "AUTHORS",
    "CHANGELOG",
    "COPYING",
    "LICENSE",
    "README",
    "UPGRADING",
    "__init__.py",
    "fabfile.py",
    "manage.py",
    "requirements.txt",
    "search_sites.py",
    "settings.py.dist",
    "urls.py",
]


def deploy():
    """
    Install all dependencies from git and pip.
    """

    install_dependencies_pip()
    install_dependencies_git()
    novnc()

def clean():
    """
    In a development environment, remove all installed packages and symlinks.
    """
    with lcd('%(doc_root)s' % env):
        gitcmd = 'git clean -%sdX -e \!settings.py'
        print('Files to be removed:')
        local(gitcmd % 'n')
        if confirm('Are you certain you would like to remove these files?'):
            local(gitcmd % 'f')
        else:
            abort('Aborting clean.')

def update():
    """
    In a development environment, update all develop branches.
    """
    require('environment', provided_by=[dev, prod])

    if env.environment != 'development':
        raise Exception('must be in a development environment in order to'
            'update develop branches.')
    else:
        with lcd('%(doc_root)s/dependencies' % env):
            for git_dir, opts in GIT_INSTALL.items():
                env.git_repo = git_dir
                if (_exists('%(doc_root)s/dependencies/%(git_repo)s' % env) and
                    'development' in opts and 'checkout' not in opts):
                    with lcd(git_dir):
                        print 'Updating git repo: %(git_repo)s' % env
                        local('git pull --ff')

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
            local('virtualenv %(virtualenv)s --distribute' % env)

            # now lets make sure the virtual env has the the newest pip
            local('%(virtualenv)s/bin/pip install -q --upgrade pip' % env)


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

    with lcd(env.doc_root):
        # Run the installation with pip, passing in our requirements.txt.
        local('%(virtualenv)s/bin/pip install -q -r requirements.txt' % env)


def install_dependencies_git():
    """
    Install all dependencies available from git.
    """

    require('environment', provided_by=[dev, prod])

    if env.environment != 'development':
        # If we can satisfy all of our dependencies from pip alone, then don't
        # bother running the git installation.
        if all(p in PIP_INSTALL for p in GIT_INSTALL):
            print 'No git repos to install! Yay!'
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

                    # Attempt to create a tracked branch and update it.
                    with settings(hide('warnings','stderr'), warn_only=True):
                        local('git checkout -t origin/%(head)s' % opts)
                        local('git pull')

        # install to virtualenv using setup.py if it exists.  Some repos might
        # not have it and will need to be symlinked into the project
        if _exists('%(doc_root)s/dependencies/%(git_repo)s/setup.py' % env):
            with lcd(env.doc_root):
                local('%(virtualenv)s/bin/pip install -q -e dependencies/%(git_repo)s' % env)

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


def novnc():
    """
    Grab noVNC.
    """

    if _exists("%(doc_root)s/noVNC" % env):
        return

    # Grab the tarball, pass it through filters. Heavy abuse of the fact that
    # shell=True in local().
    with lcd(env.doc_root):
        # -L follows redirects.
        local("curl https://github.com/kanaka/noVNC/tarball/v0.3 -L | tar xz")
        # The glob replaces a git revision.
        local("mv kanaka-noVNC-*/ noVNC")


def tarball():
    """
    Package a release tarball.
    """

    tarball = prompt('tarball name', default='ganeti-webmgr.tar.gz')
    files = ['ganeti_webmgr/%s' % file for file in env.MANIFEST]
    files = ' '.join(files)

    with lcd('..'):
        data = dict(
            tarball=tarball,
            files=files
        )
        local('tar zcf %(tarball)s %(files)s --exclude=*.pyc' % data)
        local('mv %(tarball)s ./ganeti_webmgr/' % data)


def _uncomment(filen, com):
    args = dict(filen=filen, com=com)
    local('sed -i.bak -r -e "/%(com)s/ '
          's/^([[:space:]]*)#[[:space:]]?/\\1/g" %(filen)s' % args)


def _comment(filen, com):
    args = dict(filen=filen, com=com)
    local('sed -i.bak -r -e "s/(%(com)s)/#\\1/g" %(filen)s' % args)


def ldap(state="enable"):
    """
    Enable LDAP settings, and install packages
    Depends on: libldap2-dev, libsasl2-dev
    """


    filename = 'settings.py' % env
    env.virtualenv = env.doc_root

    with lcd(env.doc_root):
        if state == "enable":
            # Install and enable LDAP settings
            if not _exists('/usr/include/lber.h'):
                abort("Make sure libldap-dev is installed before continuing")
            if not _exists('/usr/include/sasl'):
                abort("Make sure libsasl2-dev is"
                      " installed before continuing")
            local('%(virtualenv)s/bin/pip install -qr requirements-ldap.txt' % env)

            _uncomment(filename, 'from ldap_settings')
            _uncomment(filename, "'django_auth_ldap")
        elif state == "disable":
            # Disable LDAP settings and uninstall requirments
            local('%(virtualenv)s/bin/pip uninstall -qyr requirements-ldap.txt' % env)

            _comment(filename, 'from ldap_settings')
            _comment(filename, "'django_auth_ldap")
