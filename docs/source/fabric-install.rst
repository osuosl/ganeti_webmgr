Troubleshooting Fabric:
=======================

This page provides a list of common problems and errors encountered when
installing Ganeti Web Manager with Fabric, and their solutions. If you
are installing manually instead of using Fabric, please see `this
page </projects/ganeti-webmgr/wiki/Errors>`_.

If you discover ambiguities or problems with the installation
instructions that aren't addressed in this page, please ask in the
#ganeti-webmgr channel on Freenode! If you're unfamiliar with IRC,
`http://freenode.net/using\_the\_network.shtml <http://freenode.net/using_the_network.shtml>`_
can help you get started.

For installing Fabric:
----------------------

With Pip
~~~~~~~~

::

    sudo pip install fabric

On Ubuntu
~~~~~~~~~

::

    sudo apt-get install python-pip

Errors:
-------

Fabfiles
~~~~~~~~

::

    Fatal error: Couldn't find any fabfiles!

#. Are you in the ganeti\_webmgr directory?
#. Are you running version **0.7**? Check your version in the Changelog.
   **0.7** is the first release to come packaged with the fabfile. There
   will be a short interval between the publication of these
   instructions and the release of **0.7** during which install from
   Fabric will not work from the master, which is what Fabric
   automatically downloads. If you want to use Fabric before **0.7** is
   officially released, you'll need to use the develop version:
   ::

       cd ganeti_webmgr
       git pull origin develop

Can't find settings.py:
~~~~~~~~~~~~~~~~~~~~~~~

::

    Error: Can't find the file 'settings.py' in the directory containing './manage.py'. It appears you've customized things.
    You'll have to run django-admin.py, passing it your settings module.
    (If the file settings.py does indeed exist, it's causing an ImportError somehow.)

Did you remember to **cp setttings.py.dist settings.py** ?

Database Error ("no such table", "no column named *\_*",
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
etc.)
~~~~~
::

     DatabaseError at /

    no such table: django_session

or

::

    table ganeti_web_virtualmachinetemplate has no column named disks

when this error appears in your browser (with testing set to true in
your settings.py), you might be able to fix it by quitting the server
and running **./manage.py syncdb --migrate**

If the error persists, try **diff settings.py.dist settings.py**. Add
any lines from settings.py.dist to settings.py that weren't previously
there.
You could use **cp settings.py.dist settings.py**, but that would
overwrite any custom settings you've added. Then:

::

    ./manage.py reset ganeti_web
    ./manage.py syncdb --migrate

This works because reset then syncdb causes the database to be
re-created containing tables that the installed apps listed in
settings.py will need. If the app whose table was missing (such as
tastypie) was not listed in your settings.py, no table would have been
created for it.

DRBD machine creation error:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    Primary and Secondary Nodes must not match

This happens when you try to create a machine using drbd disk template
on a cluster with only one node. The template requires both a primary
and a secondary node, and if your cluster doesn't have a second node,
the 'secondary node' selection field cannot be made available. The
solution is to either add another node to your cluster, or select a
different disk template.

Instance Create error
~~~~~~~~~~~~~~~~~~~~~

::

        Instance Create

        The given name (<name of VM you're trying to create>) does not resolve: Name or service not known

Cause of Error: The name you chose for your VM broke the DNS name
resolver
Solution: Click edit at the lower right of the error screen. If you're
sure you gave it the name you want, uncheck the DNS Name Check box and
click create again. Otherwise, change the Instance Name to something
that will resolve better, leave the DNS Name Check box checked, and
click create.

OS Create Script Failed
~~~~~~~~~~~~~~~~~~~~~~~

::

    OS create script failed (exited with exit code 1)

If you get this error when creating a VM, you should try deleting the VM
and re-creating it with more disk space. A good rule of thumb is to give
Ubuntu at least 2GB.

Instance Rename
~~~~~~~~~~~~~~~

::

       Instance Rename
        Instance 'oldname.gwm.osuosl.org' not known

This error occurs when you had the DNS name check enabled when renaming
the VM.

Instance Startup
~~~~~~~~~~~~~~~~

::

        Instance Startup
        Instance 'breakthis.gwm.osuosl.org' not known

-  Diskless machines cannot start. This error sometimes happens when you
   try to.
-  Is the OS successfully installed?

Missing Templates
~~~~~~~~~~~~~~~~~

Problem: output such as **raise TemplateDoesNotExist(name)
TemplateDoesNotExist:** from either testing or trying to use the site.

Solution: If you've recently updated from the Develop branch (recently
as in 6/28/2011), you'll need to **cp settings.py.dist settings.py**
again. If you had an old settings.py, it will be looking for the
templates in the wrong place. It seeks the templates in a top-level
registration directory, when they're now actually in a sub-directory of
the ganeti\_web\_layout module.

whoosh\_index not writable for current user/group
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Situation: This can happen when running GWM through Apache.
Solution:

::

    chown apache:apache whoosh_index/
