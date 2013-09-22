===
FAQ
===

Here are some frequently asked questions, and their answers. If your question
isn't answered here, ask on the Freenode IRC network in channel
``#ganeti-webmgr`` or on the `GWM Google Group`_.

.. _GWM Google Group: http://groups.google.com/group/ganeti-webmgr/

.. contents:: List of questions
  :depth: 2
  :backlinks: none
  :local:


I added a virtual machine using the ``gnt-instance`` command-line tool, and I don't see it in GWM!
--------------------------------------------------------------------------------------------------

  Use the "Import VM" page (linked from the admin sidebar) to add those
  virtual machines to GWM.


How do I limit the resources available to a user?
-------------------------------------------------

  Change the user's quota on the cluster. Default quotas for virtual CPUs,
  disk space, and memory can be set when adding the cluster. After adding a
  user to the cluster, their quota will be listed in the "Users" tab of the
  cluster detail page. Their quota will be listed if it was set from default,
  or shown as an infinity sign if there is no existing quota. Click on the
  user's quota to add or edit the amounts of disk space, memory, and CPUs
  available to that user.


What does "Autostart" do?
-------------------------

  When the "Autostart" mark on a virtual machine's detail page is a green
  check mark, it means that the virtual machine will be automatically started
  if the node reboots. Otherwise, if the mark is a red cross, the virtual
  machine will only start when a user manually starts it.


I get the error "Whoosh\_index not writable for current user/group"
-------------------------------------------------------------------

  When running GWM through Apache, it is required that the apache user
  (or www-data) and group can write to the whoosh_index directory.

  ::

    chown apache:apache whoosh_index/
