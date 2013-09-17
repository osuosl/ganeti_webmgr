.. :changelog:

Changelog
=========

v0.10.2
-------

Notable Changes:

* Assigning owners to a VM has been changed slightly.
  * Must have admin/create_vm permissions to be an owner
  * Groups can be owners
  * Superusers can assign owner to anyone
  * Owner assignment dropdown is now sorted by name (finally)
* Users without perms on any clusters now get a 403 error if they try to go to
  the VM Creation page. Before they would get to the page but have no clusters
  to choose from.
* The 5th step of the VM Wizard composing of HVParams is now properly
  submitting the data to the RAPI
* Refresh button now refreshes data for nodes and vms instead of just the
  cluster from the RAPI.
* Hostnames are now stored in the database using all lowercase
* More validation on data retrieved from the RAPI
* Updated sshkeys scripts to be more redundant
* Fixed missing CSRF token on password reset page
* VM List pages should be consistent between the global VM list and the
  cluster VM lists

v0.10.1
-------

Notable Changes:

* Cluster defaults are now used for all steps in VM Wizard. Previously NIC
  settings and Disk size had no defaults.
* Pinned Versions of dependencies

Other:

* Fixed bug for KVM where kernel path was required, now optional. (KVM only)
* Fixed exception when owner of a VM was a group
* During VM Creation the form now properly raises a validation error if
  primary node is the same as the secondary node

v0.10
-----

Notable Changes:

* Ganeti 2.6 Support
* VM Wizard
* Job List - Cluster
* LDAP Support
* Manual Refresh Button
* Notice on Read-Only Clusters
* Sharedfile Disk Template Added

Other:

* Docs now ship with product
* Fabfile cleaned up and simplified

v0.9.2
------

* Pinned requirements at Django 1.4. Project not reviewed for Django 1.5
  compatibility.

v0.9.1
------

* New Error list page
* Pagination links now correctly show up on the Virtual Machines page
* Migrate button disabled for non-drbd VMs on VM detail page
* VM template fields correctly set NIC and DNS defaults for new VM
* Fix network devices not copied back to new VM page, when deployment fails
* Account password reset form fixed
* Error messages on VMs clearable again

v0.9
----

Notable changes:

* Django 1.4
* Ganeti 2.5 support
* Pip 1.0+ support
* Remove PyCurl dependency
* Immediate Shutdown button
* Improved installation process and documentation
* Improved RAPI functionality

Other:

* Simplified layout infrastructure
* Fix CSRF Token errors
* Transaction middleware
* Check VM hostnames for illegal characters
* New Help Tips
* Many back-end fixes to improve standards compliance and Django best practices
* Many user interface fixes and improvements

v0.8.1
------

Bugfix release.

Bugs fixed:

* CsrfResponseMiddleware removed from settings.py.dist

v0.8
----

Notable Changes:

* VM Templates
* Multiple Disks and Nics for VM Creation
* 'No Install' option for VM Creation
* CDROM2 Image Path for KVM
* User auto-complete for all username fields
* Rework and stabilisation of Jobs
* User registration is now optional
* CPU info added to node list and detail pages
* Ability to replace disks for a VM on DRBD clusters

Other:

* Cached AJAX calls
* Unified json package use (django.utils.simplejson)
* Reduced name collisions with directory reorganizing
* Cache refresh migration moved to post_migrate hook
* Unified use of CSRF tokens

v0.7.2
------

* Fixed HAYSTACK_SITECONF default setting
* Updated README to include virtualenv for mod_wsgi script


v0.7.1
------

* Updated Fabric dependency: Django Object Permissions 1.4.1
* Overview: Used resources was not displaying clusters when used did not
  permissions


v0.7
----

Notable Changes:

* Xen Support
* Internationalization Support (only greek translations.)
* Fabric & Virtual Environment deployment.
* Improved Navigation:
   * Search
   * Contextual links added to more pages
   * Breadcrumbs available on most pages
* Object log upgraded to 0.6 includes scalability improvements
* Object permissions upgraded to 1.4
   * speed improvements
   * contextual links added to generic views
   * user/group selection widget added for permission editor.
* noVNC updated to latest head, includes better support for future revisions
* Node Evacuation now works properly
* VirtualMachine owner can now be edited
* Periodic Cache updater
    * now syncronizes Nodes
    * now runs using twistd
* Nodes can now be imported through the user interface
* Various UI fixes
* Various optimizations to views to improve load times.


v0.6.2
------

* fixing packaging issue with object log

v0.6.1
------

* updating object log to 0.5.1

v0.6
----

Notable Changes:

* Nodes are now cached in the database:
* Node detail views are now available, including some admin methods
* VirtualMachines may now be edited, renamed, and migrated.
* Errors while creating virtual machines are now handled better, and can be
  recovered from
* Django Object Log is now providing logs for all objects tracked by GWM
* Admins can now add ssh keys for other users
* Virtual machine detail page has had its layout updated to be more readable
  and add more
* fixed bugs preventing syncdb working with postgresql


v0.5
----

Notable Changes:

* Status Dashboard is now the front page for GWM
    * lists cluster status for admins.
    * lists summary of virtual machines status for users.
    * lists resource usage for the user and groups.
    * error list including job failures and ganeti errors.
* Integrated NoVNC, an HTML5 + WebSockets VNC viewer
* Super users can now view resource usage and permissions for users and groups.
* Virtual machine lists are now paginated for quicker loading
* Ram and CPU quota is now based off running virtual machines
* Improved layout
* Virtual Machines list now properly works for cluster admins


v0.4
----

Initial Release

* Caching system
* Permissions system:
    * user & group management
    * per cluster/vm permissions
* basic VM management: Create, Delete, Start, Stop, Reboot
* ssh key feed
* basic quota system
* Import tools
