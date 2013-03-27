Fabric is strongly recommended
==============================

Ganeti Web Manager version 0.7 has been designed and tested for
installation with Fabric. Fabric and virtualenv solve many problems
identified in previous versions, including dependency version conflicts
and the inconvenience of installation.

Why Fabric?
-----------

`Fabric <http://docs.fabfile.org/>`_ is the Python
counterpart to the
`Capstrano <https://github.com/capistrano/capistrano/wiki>`_ web
application deployment tool. Fabric automates Ganeti Web Manager's
installation, setup, and update processes.

The fabfile contains the commands to create a virtual environment, then
download and install the correct dependencies for Ganeti Web Manager.
This standardized environment ensures that unique factors in your system
don't affect the program's tested functionality. The fabfile also
reduces the possibility of user error when installing Ganeti Web Manager
by consolidating the entire process into a single command.

::

    # production environment
    fab deploy

    # development environment
    fab dev deploy

Virtual Environments
--------------------

Ganeti Web Manager has been developed and tested with specific versions
of its :ref:`install-dependencies`.
If another program on your system uses a version of a dependency that
GWM doesn't support, it can cause failure or unexpected behavior. To
avoid these conflicts, Ganeti Web Manager version 0.7 (and above) is run
in a virtual environment.

`Virtualenv <http://www.virtualenv.org/en/latest/>`_ solves problems
caused by incorrect dependency versions by isolating the environment in
which Ganeti Web Manager is run. Fabric installs the correct versions of
the dependencies in the virtual environment, without the risk of
impeding other programs that also use the dependencies in your system's
global library. The end user's only interaction with the virtual
environment is entering it (**source venv/bin/activate**) before running GWM,
since all setup and configuration are dealt with by the Fabfile.

The virtual environment ensures that Ganeti Web Manager will access the
correct dependencies regardless of other changes that happen in your
system.

Using the Virtual Environment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    #enter virtual environment 
    source venv/bin/activate

    #leave virtual environment
    deactivate

When you are working in a virtual environment, the environment's name
appears in parentheses at the start of the command prompt. For example:

::

    user@computer:~/ganeti_webmgr$ source venv/bin/activate
    (ganeti_webmgr)user@computer:~/ganeti_webmgr$ ./manage.py syncdb
    (ganeti_webmgr)user@computer:~/ganeti_webmgr$ deactivate
    user@computer:~/ganeti_webmgr$ 

Using The Virtual Environment with Apache and mod\_wsgi
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The virtual environment must be activated for use with mod\_wsgi. This
is done by executing the **activate\_this** script generated when a
virtualenv is created. The following code should be in the
**django.wsgi** file apache is configured to use.

::

    # activate virtual environment
    activate_this = '%s/venv/bin/activate_this.py' % PATH_TO_GANETI_WEBMGR
    execfile(activate_this, dict(__file__=activate_this))
