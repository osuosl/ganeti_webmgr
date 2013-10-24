.. _development:

===============
Developer Guide
===============

This guide is intended to help you begin writing code and documentation for the |gwm| project. Please read the :ref:`OSL Development Process <process>` for information on how this project is managed and what we do to review and integrate code into the master repository. Please read the entire guide before beginning work, we will not be able to accept contributions that don't follow these guidelines and standards.

For information on our release cycle and versions, please see :ref:`release`.


Issue Tracking
--------------

The bug tracker for |gwm| is at `code.osuosl.org`_, and all bugs and feature requests for |gwm| should be tracked there. Please create an issue for any code, documentation or translation you wish to contribute.

Please see the :ref:`issues` for details on how to create informative issues.

.. _`code.osuosl.org`: https://code.osuosl.org/projects/ganeti-webmgr


Get the Code
------------

From OSL's repository:

::

    git clone git://git.osuosl.org/gitolite/ganeti/ganeti_webmgr

Note that this is a read-only clone, commit access requires an account on our gitolite server. You must be `Submitting Code`_ and establish a relationship with us prior to being granted commit access. 

When you have write access:

::

    git clone git@git.osuosl.org:ganeti/ganeti_webmgr


From Github, you can `clone or fork from our repository mirror`_.

.. _`clone or fork from our repository mirror`: https://github.com/osuosl/ganeti_webmgr


Repository Layout
-----------------

We loosely follow `Git-flow <http://github.com/nvie/gitflow>`_ for managing repository. Read about the `branching model <http://nvie.com/posts/a-successful-git-branching-model/>`_ and why `you may wish to use it too <http://jeffkreeftmeijer.com/2010/why-arent-you-using-git-flow/>`_.


-  **master** - Releases only, this is the main public branch.
-  **release/<version>** - A release branch, the current release branch is tagged and merged into master.
-  **develop** - Mostly stable development branch. Small changes only. It is acceptable that this branch have bugs, but should remain mostly stable.
-  **feature/<issue number>** - New features, these will be merged into develop when complete.
-  **bug/<issue number>** - Bug fixes.
-  **enhancement/<issue number>** - Enhancements to existing features.
   
See :ref:`issues` for more information on issue types.

When working on new code, be sure to create a new branch from the appropriate place:

-  **develop** - if this is a new feature
-  **release/<version>** - if this is a bug fix on an existing release


Code Standards
--------------

PEP8
''''

We follow `PEP 8 <http://www.python.org/dev/peps/pep-0008/>`_, "the guide for python style".

In addition to PEP 8:

-  Do not use backslash continuations. If a line must be broken up, use parenthetical continuations instead.

Units
'''''

Try to write modular code. Focus on isolating units of code that can be easily analyzed and tested. For sanity purposes, please try to avoid mutually recursive objects.

JSON
''''

If you need a JSON library, the import for this code base is "from django.utils import simplejson as json". See `#6579 <http://code.osuosl.org/issues/6579>`_ for more information.


Dev Environment
---------------

Writing and testing code is made much easier by the right tools and a development environment that mirrors a production environment. To begin working with |gwm| code, you will need Git, Python 2.6+, and `Python VirtualEnv`_. We also recommend VirtualBox_ and Vagrant_, a scripting front-end to VirtualBox to set up a virtual cluster to test your code with. 

.. _`Python VirtualEnv`: http://www.virtualenv.org/en/latest/
.. _`VirtualBox`: https://www.virtualbox.org/
.. _`Vagrant`: http://www.vagrantup.com/


Git
'''

If you are unfamiliar with Git, please read the `official Git tutorial`_ or `this excellent tutorial`_.

There are many graphical Git UIs, if you are not comfortable working with Git on the command line. See `this list of Git GUI clients`_ for more information.

.. _`official Git tutorial`: http://git-scm.com/docs/gittutorial
.. _`this excellent tutorial`: http://www.vogella.com/articles/Git/article.html
.. _`this list of Git GUI clients`: http://git-scm.com/downloads/guis


Virtualenv and Pip
''''''''''''''''''

|gwm|'s install script uses the Python VirtualEnv utility to create a local environment in which to install all of GWM's Python dependencies, and GWM itself runs from within this environment. To run tasks with manage.py, or to work with the python console on GWM code, you will need to activate the environment in your shell:

::  

    source /path/to/gwm/venv/bin/activate


Note that the environment will only be active for the terminal in which this command is run. 

Pip is used to install packages to the currently active Python environment. If you would like to install python packages for debugging or to add functionality to |gwm|, be sure the |gwm| virtual environment is active and install packages:

::

    pip install packagename


If you are adding python packages to add functionality or to support |gwm| features you are adding, be sure to add the package to requirements.txt. You can get a list of all python packages installed in your current environment with

::

    pip freeze

Add your package name to requirements.txt and commit this with the rest of your code. For more information on Pip and package name/version specifications, see (a link to pip docs)
    

VirtualBox and Vagrant
''''''''''''''''''''''
    
Virtual machines provide an easy way to deploy a Ganeti cluster to test |gwm| with, or for use as a self-contained dev environment that can be shared with other developers. VirtualBox is a free virtualization platform available on Windows, Linux, and MacOS. Vagrant is a scripting front end for VirtualBox that allows easy creation, provisioning, and management of VirtualBox VMs. 

Development VM
~~~~~~~~~~~~~~

|gwm| now ships with a Vagrantfile that will launch a headless VirtualBox vm.

.. todo::
    insert information on how and why you might use this

Ganeti Test Cluster
~~~~~~~~~~~~~~~~~~~

To test new code in |gwm| it is often necessary to have a Ganeti cluster to manage. Using Vagrant, a virtual multi-node cluster can easily be created:

- clone https://github.com/ramereth/vagrant-ganeti.git
- add the following to your hosts file :
::

    33.33.33.10 ganeti.example.org
    33.33.33.11 node1.example.org
    33.33.33.12 node2.example.org
    33.33.33.13 node3.example.org

- enter the vagrant-ganeti directory and type
::

    vagrant up node1

Vagrant will download, spin up, and provision a virtual machine with Ganeti installed and ready to use. You can now add the ganeti.example.org cluster from the |gwm| and create virtual machine instances on it. To spin up additional nodes, simply:
::

    vagrant up node2
    vagrant up node3

See the `vagrant-ganeti page`_ for more details.

.. _`vagrant-ganeti page`: https://github.com/ramereth/vagrant-ganeti

Adding features
---------------

When adding a feature to GWM, please remember to include:

Help tips
'''''''''

The gray box with a green title bar that appears on the right side of the page when you focus on a form field is a help tip. To add one for a new field, add it to the file which corresponds to your field's form in the ganeti\_web/templates/ganeti/helptips/ directory.

Internationalization
''''''''''''''''''''

Ganeti Web Manager is designed to support translation to other languages using Django's i18n machinery. If you add text that will be displayed to the user, please remember to format it for translation:
::

    {% trans "this text will be displayed in the correct language" %}

    {% blocktrans %}
        Here is a some text that will be displayed
        in the correct language but would not
        fit well in a single line
    {% endblocktrans %}

`Django's i18n page <https://docs.djangoproject.com/en/dev/topics/i18n/>`_ has more
information about this.

Fixing Bugs
-----------

When bugs are fixed, the issue should be updated with a clear description of the nature of the bug, the nature of the fix, and any additional notes that will help future developers understand the fix.

Before working on a bug fix, determine if the faulty code is covered by a unit test. If so, and the test did not reveal the flaw, update the test appropriately. If no test exists, it should be written if possible. The test should be submitted along with the fixed code.

Writing Tests
-------------

The following are general guidelines. For specific details on how to write |gwm| tests, please see See :ref:`testing`. 

Ganeti Web Manager has a fairly complete test suite. New code should have matching tests. Before committing code, run the suite for Ganeti Web Manager and `Object Permissions <http://code.osuosl.org/projects/object-permissions>`_

::

    ./manage.py test ganeti_web
    ./manage.py test object_permissions


Clean up after yourself
'''''''''''''''''''''''

Remember to tear down any resources you set up in your tests. Don't use "YourModel.objects.all().delete()" to clean up your objects; it could be hiding bugs. Clean up exactly the resources you created.

Test your setups and teardowns
''''''''''''''''''''''''''''''

To speed up analysis of broken tests, if you have a setUp() or tearDown() in a TestCase, add a test\_trivial() method which is empty. It will pass if your setUp() and tearDown() work.

Views
'''''

All views should be thoroughly tested for security, checking to ensure that the proper HTTP codes are returned.

-  Test Anonymous User access
-  Test Permission based access
-  Test Superuser based access

Check for invalid input.

-  missing fields
-  invalid data for field

Templates & Javascript
''''''''''''''''''''''

The test suite does not yet include full selenium tests for verifying Javascript functionality. Some basic tests can be performed using Django's test suite:

-  Check objects in the context: forms, lists of objects, etc.
-  Check for existence of values in forms.

See :ref:`selenium` for more information on what Selenium can test within GWM.



Writing Documentation
---------------------

Documentation exists as RestructuredText files within the GWM repository, and as in-line comments in the source code itself.

Sphinx
''''''

The docs/ directory contains the full tree of documentation in RestructuredText format. To generate the docs locally, make sure you have activated the |gwm| virtual environment, and that Sphinx is installed.

::
    
    pip install Sphinx
    cd docs
    make html

HTML documentation will be generated in the build/html directory. For information on generating other formats, see the `Sphinx documentation`_.

.. _`Sphinx documentation`: http://sphinx-doc.org/

The documentation for |gwm| is divided into several sections:

- Features: Descriptions of features and their implementation
- User Guide: How to use GWM and its various features
- Development Guide: How to work on the GWM code (this document)
- Info: Various information on the project itself
- Reference: General information referred to in other docs


Usage of features should be documented in the usage/ directory. Each distinct unit of functionality should have a separate file, for instance "create a new virtual machine" should have a single file documenting how to create a new virtual machine. Overview documents, for example "managing virtual machines" will reference or include these sub files.

Implementation and structural details of features should be documented in the features/ directory, one file per distinct feature. This documentation should give an overview of the functionality, rational and implementation of the feature - for example, documenting how the "add virtual machine" view generates a request to the RAPI.

Any changes or enhancements to an existing feature should be documented in the feature's documentation files.

Development documentation should be updated when any changes are made to the development process, standards, or implementation strategies.

In-line Docs
''''''''''''

All methods in the source code should be commented with doc strings, including parameters, return values, and general functionality.

.. todo::
    add standards for inline docs

Submitting Code
---------------

Please read :ref:`process` for details on how we triage, review and merge contributed code. 


Patches
'''''''

Patches should either be attached to issues, or emailed to the mailing list. If a patch is relevant to an issue, then please attach the patch to the issue to prevent it from getting lost.

Patches must be in git patch format, as generated by git format-patch.

::

    git commit
    git format-patch HEAD^

To create patches for all changes made from the origin's master branch, try:

::

    git format-patch origin/master

For more information, see the man page for git-format-patch.

Sending emails to the list can be made easier with git send-mail; see the man page for git-send-email for instructions on getting your email system to work with git.

Pull Requests
'''''''''''''

If there are multiple patches comprising a series which should be applied all at once, git pull requests are fine. Send a rationale for the pull request, along with a git pull URL and branch name, to the mailing list.

Git Write Access
''''''''''''''''

Contributors in good standing who have contributed significant patches and who have shown a long-term commitment to the project may be given write access to our repository. Such contributors must follow our :ref:`process`, including participating in code review and planning.


Submitting Documentation
------------------------

Documentation is just as much a part of the project as code, and as such you can contribute documentation just as outlined above for code. See `Writing Documentation`_ for details on the documentation tree.

If you are not comfortable with git, patches or pull requests, you may submit documentation via a text file sent to the mailing list or attached to an issue. We recommend creating an issue, as this helps us keep track of contributions, but the mailing list is an excellent place to solicit feedback on your work.

Submitting Translations
-----------------------

Translations should be submitted via patches, a pull request, or by attaching a .po file to an issue. We recommend cloning the git repository and using django-admin.py makemessages to find all the available strings for translation. If you find strings in the UI that are not available for translation, patches to fix this condition are much appreciated. As with all contributions, we recommend creating a new issue on our issue tracker for your work.

For details on how to write translation strings and how to make use of them, please see `Django's i18n page <https://docs.djangoproject.com/en/1.4/dev/topics/i18n/>`_ 
