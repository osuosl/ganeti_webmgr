.. _virtual-environment:

Virtual environment
===================

A |venv| is a "space" separated from operating system, where
Python packages get installed.  This "space" is local, thus prevents Python
packages from overwriting your system Python packages.

Imagine having package ``xyz`` in version ``1.2.4`` installed system-wide.  Now
you want to install |gwm|, that requires this package in version ``1.1``.

You can't keep both packages installed system-wide.  Therefore you need to
somehow separate packages required by |gwm| and your system packages.  Virtual
environment does exactly this.

Virtual environment structure
-----------------------------

Virtual environment (shortly ``virtualenv`` or ``venv``) consists of these
directories:

* ``bin`` - contains executable files and activation scripts
* ``include`` - contains symlink to ``lib/python2.x`` directory
* ``lib`` - Python packages get installed to this directory
* ``local`` - contains symlinks to ``bin``, ``include`` and ``lib`` directories
* ``share`` - contains documents and ``man`` pages installed along with Python
  packages

Helpers and tools
-----------------

Main tool used for creating virtual environments is ``python-virtualenv`` and
it's executable: ``virtualenv``.

When you issue ``virtualenv name`` in your shell, this tool creates structure
described above in the ``name`` directory.

Usually next thing to do when developing (or deploying) a project in Python is
to clone a repository **within that virtual environment**.  It creates your
project files next to |venv|'s directories.  And everything becomes a mess.

To help overcome this mess, someone clever wrote ``virtualenvwrapper``.  This
is a set of shell scripts, that:

* create |venv| in your ``$HOME/.virtualenvs`` directory
* list virtual environments existing there
* remove specified |venv|
* quickly switch between existing virtual environments

...and we **highly recommend** using it.

``virtualenvwrapper`` commands
------------------------------

``mkvirtualenv name``
  Creates |venv| with given *name*.

``lsvirtualenv``
  List all existing virtual environments.

``rmvirtualenv name``
  Remove existing |venv| with given *name*.

``workon name``
  Switch to |venv| with given *name*.

``deactivate``
  When you're within |venv|, you can leave it by issuing this command.

Command line prompt
-------------------

By default, after activating specific |venv|, it's name appears at the
beginning of your shell prompt.  For example::

  $ cd ganeti_webmgr
  $ workon gwm
  (gwm)$ gwm-manage.py --help
  ...
  (gwm)$ deactivate
  $ lsvirtualenv

.. note::
  In some guides in this documentation these brackets indicate commands issued
  from within |venv|.

.. |venv| replace:: virtual environment
