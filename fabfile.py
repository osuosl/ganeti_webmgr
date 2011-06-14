import os
from fabric.api import env
from fabric.context_managers import cd, settings, hide, lcd
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

PIP_INSTALL = {
    'django'                    :'>=1.3',
    'django-registration'       :'',
    'south'                     :'',
    'django-haystack'           :'==1.2.1',
    'whoosh'                    :'>=1.8.1',
    'django_object_permissions' :'=1.3.1',
    'twisted'                   :'>=11.0.0'
}

GIT_INSTALL =  {
    'noVNC':{
        'url':'git://github.com/kanaka/noVNC.git',
        'development':'3859e1d35cf',
        'production':'3859e1d35cf',
        },
    'django_object_permissions':{
        'url':'git://git.osuosl.org/gitolite/django/django_object_permissions',
        'development':'develop',
        'symlink':'object_permissions',
        },
    'django_object_log':{
        'url':'git://git.osuosl.org/gitolite/django/django_object_log',
        'development':'develop',
        'symlink':'object_log'
        },
    'django_muddle_users':{
        'url':'git://git.osuosl.org/gitolite/django/django_muddle_users',
        'development':'develop',
        'symlink':'muddle_users'
    }
}


# default environment settings - override these in environment methods if you
# wish to have an environment that functions differently
env.doc_root = '.'
env.remote = False


def dev():
    """ configure development deployment """
    env.environment = 'development'


def prod():
    """ configure a production deployment """
    env.environment = 'production'


# Files and directories that will be included in tarball when packaged
env.MANIFEST = [
    "django_test_tools",
    "deprecated",
    "ganeti_web",
    "i18n",
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
    "urls.py"
]


def deploy():
    """
    Install all dependencies from git and pip
    """
    install_dependencies_pip()
    install_dependencies_git()


def _exists(path):
    """
    helper to see if a path exists.  uses either os.exists or exists depending
    on if the environment is remote or local
    """
    if env.remote:
        return exists(path)
    else:
        return os.path.exists(path)


def create_virtualenv(virtualenv=None, force=False):
    """ create a virtualenv for pip installs """
    require('environment', provided_by=[dev, prod])
    env.virtualenv = virtualenv if virtualenv else env.doc_root
    
    with lcd(env.doc_root):
        if not force and _exists('%(virtualenv)s/lib' % env):
            print 'virtualenv already created'
        else:
            local('virtualenv %(virtualenv)s' % env)


def create_env():
    """
    setup environment for git dependencies
    """
    require('environment', provided_by=[dev, prod])

    with lcd(env.doc_root):
        if _exists('dependencies'):
            print 'dependencies directory exists already'
        else:
            local('mkdir dependencies')


def install_dependencies_pip():
    """
    Install all dependencies available from pip
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
        #XXX create temp requirements file text from list of requirements
        #    it will be destroyed after install is complete
        requirements = '\n'.join([''.join(p) for p in pips_.items()])
        with settings(hide('running')):
            local("echo '%s' > requirements.txt" % requirements)

        local('pip install -E %(virtualenv)s -r requirements.txt' % env)
        local('rm requirements.txt')


def install_dependencies_git():
    """ Install all dependencies available from git """
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
        elif env.environment == 'dev' and 'production' in opts:
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

        # install using virtualenv if configured to do so
        if 'virtualenv' in opts and opts['virtualenv']:
            with lcd(env.doc_root):
                local('pip install -e dependencies/%s' % name)

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
    """ package a release tarball """
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
