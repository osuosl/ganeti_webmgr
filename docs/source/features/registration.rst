.. _registration:

Open Registration
=================

Ganeti Web Manager versions 0.8 and above allow you to choose whether
users can create their own accounts, or need to be added by an
administrator.

The default setting for registration is open, which means that visitors
to your site's login page can follow a link from the login page to
create their own accounts.

.. figure:: /_static/registration-link.png
   :align: center

The "Not a member?" link takes the user to the registration page:

.. figure:: /_static/registration-page-open.png
   :align: center

The user is emailed a password and a confirmation link, then has an
account on your site. Users can also be added by a site admin by
selecting the users link in the admin toolbar, then using the Add User
button to reach the user creation form.

Closing Registration
--------------------

In some contexts, users should not be able to create their own accounts.
To implement this, simply change the ``ALLOW_OPEN_REGISTRATION`` setting
in your ``gwm_config.py`` file to False::

  # Whether users should be able to create their own accounts.
  # False if accounts can only be created by admins.
  ALLOW_OPEN_REGISTRATION = False

Result of closed registration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The "Not a member?" link is hidden from users on the login page. If they
navigate to the ``<SITE_ROOT>/accounts/register`` page, they will see this
message instead of the account creation form:

.. figure:: /_static/closed-registration.png
   :align: center
