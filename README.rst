==================
Ganeti Web Manager
==================

Ganeti Web Manager is a Django-based web application that allows administrators
and clients access to their ganeti clusters.

Building the Documentation
==========================

Our documentation is written in ReStructuredText and built using Sphinx. First
you will need to install the dependencies to a virtualenv or to your system's
python installation::

  pip install -r requirements/dev.txt

Then you will need to run the following commands to build the documentation::

  cd docs/
  make html

The documentation will be located at ``docs/build/html/`` as html files.
If you open ``index.html`` with your web browser, it will take you to the
table of contents.


Installation
------------

For installation instructions please refer to our installation_ documentation.


Compatibility
-------------

For a list of versions, and browsers supported by |gwm| check our compatibility_ documentation.


Dependencies
------------

A list of dependencies can be found in our requirements_ documentation.

Links
-----

* `Project page <http://code.osuosl.org/projects/ganeti-webmgr>`_
* `Documentation <http://ganeti-webmgr.readthedocs.org/en/latest/>`_
* `Mailing List <http://groups.google.com/group/ganeti-webmgr>`_
* `Twitter <http://twitter.com/ganetiwebmgr>`_
* IRC: ``#ganeti-webmgr`` on freenode.net

.. _installation: http://ganeti-webmgr.readthedocs.org/en/develop/getting_started/installing.html
.. _compatibility: http://ganeti-webmgr.readthedocs.org/en/develop/project_info/compatibility.html
.. _requirements: http://ganeti-webmgr.readthedocs.org/en/develop/getting_started/requirements.html

.. |gwm| replace:: Ganeti Web Manager
