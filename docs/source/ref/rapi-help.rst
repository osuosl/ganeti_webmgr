.. _rapi:

Working With The RAPI
=====================

There are several places to view documentation detailing how to
interface with the python RAPI, though none of them are comprehensive.

The following is a list of five different sources where information
relating to the RAPI can be found.

#. The Ganeti RAPI PyDocs_ 
#. The Ganeti RAPI `HTML Docs`_
#. The gnt-instance man-page_
#. The rapi client_ code contained in the upstream_ ganeti project
#. The rapi-tests_ which are also contained in the upstream_ ganeti project

.. _PyDocs: http://docs.ganeti.org/ganeti/current/api/py/ganeti.rapi.client.GanetiRapiClient-class.html
.. _`HTML Docs`: http://docs.ganeti.org/ganeti/current/html/rapi.html
.. _man-page: http://docs.ganeti.org/ganeti/current/man/gnt-instance.html
.. _client: http://git.ganeti.org/?p=ganeti.git;a=blob;f=lib/rapi/client.py;hb=HEAD
.. _upstream: http://git.ganeti.org/?p=ganeti.git;a=summary
.. _rapi-tests: http://git.ganeti.org/?p=ganeti.git;a=blob;f=test/ganeti.rapi.client_unittest.py;hb=HEAD

RAPI in a Python Shell
----------------------

Start up a python shell using the ``manage`` django script.
::

    $ ./manage.py shell

In the python shell import ``client.py`` from ``util``.
::

    >>> from util import client

Assign a variable to the rapi client and pass in the name of the cluster
as a string to the GanetiRapiClient object.
::

    >>> rapi = client.GanetiRapiClient('my.test.cluster')

-  Note - For R/W access to the cluster you need to pass in 'username'
   and 'password' as kwargs to the GanetiRapiClient object. Replace
   USERNAME and PASSWORD with the correct cluster R/W credentials
   ::

       >>> rapi = client.GanetiRapiClient('my.test.cluster', username='USERNAME', password='PASSWORD')

-  Optional - Setup PrettyPrinter to prettify the output of RAPI
   functions that return dictionaries.
   ::

       >>> import pprint
       >>> pp = pprint.PrettyPrinter(indent=4).pprint

   Now you are able to prettify output like this:
   ::

       >>> pp(rapi.GetInfo())

-  RAPI commands can now be accessed as functions of the rapi variable.
   ::

       >>> rapi.GetInstance('my.test.instance')
