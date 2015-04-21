.. _search

About the search system
=======================

The search system in Ganeti Web Manager utilizes three main
technologies:

-  `Haystack <http://haystacksearch.org/>`_ - A model-based search
   system for Django
-  `Whoosh <https://bitbucket.org/mchaput/whoosh/wiki/Home>`_ - A
   pure-Python indexing and searching library
-  `jQuery UI Autocomplete
   widget <http://jqueryui.com/demos/autocomplete/>`_ - Displays
   suggestions to input boxes as the user types

Below, I will discuss the different components of the search system.

Haystack
--------

Haystack is the meat 'n' potatoes of the search system, involved in
every aspect. Mainly it does the following:

-  Defines the search set in terms of GWM models in **/ganeti_web/search_indexes.py**
-  Manages making queries and indexing the search back-end (currently
   Whoosh).
-  Provides search-specific forms and templates (GWM only uses one
   search result template: **/templates/search/search.html**)

Find out more about defining search indexes with the `Haystack
SearchIndex
API <http://docs.haystacksearch.org/dev/searchindex_api.html>`_. To find
out more about Haystack in general, see `its
documentation <http://docs.haystacksearch.org/dev/>`_.

Whoosh
------

Whoosh is a pure-Python indexing and searching library that Haystack
uses as a search back-end. The developer actually doesn't need to
interact with Whoosh directly.

Of indexing and DB performance
------------------------------

Haystack is currently set to do live indexing. This means that the
search index gets updated every time an included model is updated in the
database. This means the index will always be up-to-date, but has the
potential to severely hamper performance when dealing with a lot of
database changes.

Indexing behavior is set when the search set is defined in
**ganeti_webmgr/ganeti_web/search_indexes.py**

If database performance starts to become an issue, try using
*SearchIndex* instead of *RealTimeSearchIndex*, and run::

    $ django-admin.py update_index

from time-to-time. For more information,
please see the `Haystack documentation on the
subject <http://docs.haystacksearch.org/dev/searchindex_api.html#keeping-the-index-fresh>`_.

jQuery UI Autocomplete widget
-----------------------------

The Autocomplete widget suggests search results in real-time as the user
types a query. This is facilitated through two main components:

-  `jQuery UI Autocomplete
   widget <http://jqueryui.com/demos/autocomplete/>`_ itself
-  An autocomplete Django view **ganeti_web/views/search.py**
   that supplies Autocomplete with suggestion data to display

Basically, the Autocomplete widget calls the autocomplete view as the
user types, and fills a pop-up box underneath the input box with search
suggestions. The JavaScript logic can be found in **/static/js/autocomplete_search.js**,
and the search view can be found in **ganeti_web/views/search.py**.
Both of these files contain details about how the suggestion data is
structured, sent, and processed.
