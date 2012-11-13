Errors & Troubleshooting
========================

The main Ganeti install page assumes significant background knowledge,
especially regarding troubleshooting. This page provides guidance about
common errors that occur during the installation process. This page is
structured to supplement the :doc:`manual-install` guide.

For help with problems related to installing Ganeti Web Manager with
Fabric, please see :doc:`fabric-install`.

If you discover ambiguities or problems with the installation
instructions that aren't addressed in this page, please ask in the
#ganeti-webmgr channel on Freenode! If you're unfamiliar with IRC,
`http://freenode.net/using\_the\_network.shtml <http://freenode.net/using_the_network.shtml>`_
can help you get started.

Get The Code
------------

Step 3 -- mkdir ganeti\_webmgr\_lib
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

If you skip this step, you will be unable to copy and paste the commands
from later sections, because they will refer to a location that doesn't
exist. If you realize later that you forgot to create this directory, it
will still be possible to complete the installation and run the server
without problems. You will have to change any commands that include
**ganeti\_webmgr\_lib** to reflect the actual location of
**object\_permissions** and **object\_log** if you clone them into your
home directory, though.

Step 5 -- Creating Symbolic Links
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

After following the install instructions, you should check that the
symlinks worked correctly. Here's an example where object\_log didn't
link correctly (object\_permissions shows how a valid symlink looks):

.. figure:: /_static/broken_vs_working_symlinks.png
   :align: center
   :alt: Picture of one broken and one working symlink in bash

   Picture of one broken and one working symlink in bash

To fix it, figure out where the django\_object\_log directory is -- you
might have accidentally put it in your home folder instead of
**ganeti\_object\_lib**. Now cd back into **ganeti\_webmgr** to remove
the broken link and replace it with a good one:

::

    rm object_log
    ln -s ../django_object_log/object_log .

The django\_object\_log/object\_log part of the ln command should be the
path from your home directory to the location of object\_log.

Optional (for the web-based VNC console)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

::

    fatal: The remote end hung up unexpectedly

The remote end hangs up when it gets an input telling it to return a
file that isn't there. Check everything for typos and try again.

Configuration
-------------

Step 3 -- **syncdb**
~~~~~~~~~~~~~~~~~~~~

::

    Error: No module named object_log
    Error: No module named object_permissions

Either of these errors means that a symlink is broken. Step 5 under Get
The Code, above, explains how to fix this.

401 Unauthorized: No permission -- see authorization schemes
------------------------------------------------------------

This error occurs when your cluster is not :doc:`usage/clusters`, or the user
credentials are incorrect.
