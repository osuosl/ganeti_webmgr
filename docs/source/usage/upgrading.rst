.. _upgrading:

Upgrading
=========

.. note::
  Please read the instructions fully before starting. The order of operations
  is important. The upgrade may fail if done out of order.

.. warning::
  This guide is intended for |gwm| in versions 0.11 and higher.  If you have
  older installation that you want to upgrade, please read carefully
  :ref:`old_upgrading` page.

This guide will walk you through upgrading Ganeti Web Manager. Our upgrade
process uses `South <http://south.aeracode.org/docs/>`_, a database migration
tool that will update your database.

1. Back up the database
2. Make sure newest |gwm| is available in OSUOSL repository at
   http://ftp.osuosl.org/pub/osl/ganeti-webmgr/
3. Run your :ref:`setup script <setup-script>` with ``-u ./gwm_venv`` argument.

Follow the guide for your version.

0.11 and later
--------------

Since 0.11, |gwm| uses :ref:`special setup script <setup-script>` for
installing and upgrading.

By using this script (and due to other major changes in |gwm| architecture),
you now have to use different management script.  It gets installed into
|gwm|'s virtual environment as ``django-admin.py``. Once you've activated your
virtual environment, it will be in your path.

In order to upgrade your database run::

  $ django-admin.py migrate --delete-ghost-migrations --settings "ganeti_webmgr.ganeti_web.settings"


Updated settings
----------------

0.11
~~~~

Settings now have a few ways of configuring, designed to make life easier for
those deploying |gwm|, especially if your unfamilar with python.

Settings now live in ``/opt/ganeti_webmgr/config/config.yml``. You can now use
yaml to configure your settings. By default this config file does not exist, so
be sure to create add your config file there.

An example yaml config file can be found in the
`configuration <configuring>`_ documentation, and can also be found in
``ganeti_webmgr/ganeti_web/settings/`` in a file named ``config.yml.dist``.

If you prefer configuration using the typical django ``settings.py`` file, fear
not, that will still work, however it has changed a bit.

You will need to remove any imports of other settings files from it, and you
will need to add it to the ``ganeti_webmgr/ganeti_web/settings/`` folder as
``settings.py``. Take a look at ``settings.py.dist`` in that same folder for an
example.
