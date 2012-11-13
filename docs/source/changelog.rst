CHANGELOG
=========

v0.6.1
------

Updating Django Object Log to 0.5.1

v0.6
----

Notable Changes:
^^^^^^^^^^^^^^^^

-  Nodes are now cached in the database:
-  Node detail views are now available, including some admin methods
-  VirtualMachines may now be edited, renamed, and migrated.
-  Errors while creating virtual machines are now handled better, and
   can be recovered from
-  Django Object Log is now providing logs for all objects tracked by
   GWM
-  Admins can now add ssh keys for other users
-  Virtual machine detail page has had its layout updated to be more
   readable and add more
-  fixed bugs preventing syncdb working with postgresql

Tickets
^^^^^^^

-  `#987 <http://code.osuosl.org/issues/987>`_ **Feature** VM: Modify settings
-  `#2661 <http://code.osuosl.org/issues/2661>`_ **Feature** VM Migration
-  `#2703 <http://code.osuosl.org/issues/2703>`_ **Feature** Nodes: Implement RAPI features
-  `#2715 <http://code.osuosl.org/issues/2715>`_ **Feature** Nodes: change roles
-  `#2727 <http://code.osuosl.org/issues/2727>`_ **Feature** Nodes: evacuate button
-  `#3309 <http://code.osuosl.org/issues/3309>`_ **Bug** Overview: missing/import links
   swapped
-  `#3423 <http://code.osuosl.org/issues/3423>`_ **Bug** Migrate incorrectly sets cleanup=true
-  `#3435 <http://code.osuosl.org/issues/3435>`_ **Bug** Nodes: Modify role lacks node, force
   args
-  `#3447 <http://code.osuosl.org/issues/3447>`_ **Bug** Conflicts between required fields for
   VirtualMachineTemplate and NewVirtualMachineForm and
   ModifyVirtualMachineForm
-  `#3471 <http://code.osuosl.org/issues/3471>`_ **Feature** SSH Keys: Cluster support in
   sshkeys.py
-  `#3489 <http://code.osuosl.org/issues/3489>`_ **Bug** VirtualMachine create is not checking
   for unique hostnames
-  `#3549 <http://code.osuosl.org/issues/3549>`_ **Bug** Add GPL header to files
-  `#3555 <http://code.osuosl.org/issues/3555>`_ **Bug** Reboot VirtualMachine log message is
   returning an error
-  `#3621 <http://code.osuosl.org/issues/3621>`_ **Bug** Migrate buttons showing when user
   doesn't have access
-  `#3651 <http://code.osuosl.org/issues/3651>`_ **Bug** Admins adding ssh key to another user
   adds the sshkey to their own profile
-  `#3657 <http://code.osuosl.org/issues/3657>`_ **Bug** Pulling ssh keys for a VM produces an
   error
-  `#2841 <http://code.osuosl.org/issues/2841>`_ **Feature** Allow reinstall when create fails
-  `#3225 <http://code.osuosl.org/issues/3225>`_ **Feature** SSH keys view for all keys
-  `#3285 <http://code.osuosl.org/issues/3285>`_ **Bug** VM Edit shouldn't always require
   reboot
-  `#3315 <http://code.osuosl.org/issues/3315>`_ **Bug** VM Reinstall: Job always displaying
   "shutdown"
-  `#3357 <http://code.osuosl.org/issues/3357>`_ **Feature** virtual machine detail view
   should use an installation progress template
-  `#3399 <http://code.osuosl.org/issues/3399>`_ **Bug** Add "Free" to Memory/Disk column
   labels on overview page
-  `#3411 <http://code.osuosl.org/issues/3411>`_ **Bug** Template error when creating a VM
   with DRBD
-  `#3417 <http://code.osuosl.org/issues/3417>`_ **Bug** JSON output not displaying when doing
   a reinstall or create
-  `#3441 <http://code.osuosl.org/issues/3441>`_ **Bug** Nodes: Incorrect wording for evacuate
-  `#3213 <http://code.osuosl.org/issues/3213>`_ **Bug** Create form does not remember values
   when errors are reached
-  `#3243 <http://code.osuosl.org/issues/3243>`_ **Bug** When deleting someones permissions
   frmo cluster/vm the html row is not removed
-  `#3465 <http://code.osuosl.org/issues/3465>`_ **Bug** clearing the job error from a failed
   create results in vm that cannot be recovered by a user
-  `#3513 <http://code.osuosl.org/issues/3513>`_ **Bug** Nodes: Setting node to offline
   results in a traceback
-  `#3531 <http://code.osuosl.org/issues/3531>`_ **Bug** Change "Failover Node" to "Secondary
   Node" on VM Detail page
-  `#3561 <http://code.osuosl.org/issues/3561>`_ **Bug** Log messages that can involve a Group
   in place of a User are not rendered correctly
-  `#789 <http://code.osuosl.org/issues/789>`_ **Feature** VM Creation - add network boot
   device
-  `#2667 <http://code.osuosl.org/issues/2667>`_ **Feature** Add templates and keys to LogItem
-  `#2673 <http://code.osuosl.org/issues/2673>`_ **Feature** create generic view for
   displaying LogItems for a given object
-  `#2679 <http://code.osuosl.org/issues/2679>`_ **Feature** need to log virtualmachine
   reinstallation actions
-  `#2691 <http://code.osuosl.org/issues/2691>`_ **Feature** VM: Rename
-  `#2709 <http://code.osuosl.org/issues/2709>`_ **Feature** Nodes: Node Detail Tab
-  `#2721 <http://code.osuosl.org/issues/2721>`_ **Feature** Nodes: migrate button
-  `#2901 <http://code.osuosl.org/issues/2901>`_ **Bug** CD-ROM selected as Create VM Boot
   Device
-  `#3105 <http://code.osuosl.org/issues/3105>`_ **Feature** form dropdowns replaced with
   single choice should be formatted better
-  `#3123 <http://code.osuosl.org/issues/3123>`_ **Bug** Modify Instance: disk\_type fails
-  `#3129 <http://code.osuosl.org/issues/3129>`_ **Bug** CreateVM: CD-ROM Image Path needs to
   check for http
-  `#3135 <http://code.osuosl.org/issues/3135>`_ **Feature** Create VM: Only show VM Image
   Path if CD-ROM is selected as a boot device
-  `#3159 <http://code.osuosl.org/issues/3159>`_ **Bug** VM: users with only tags/modify
   should at least see overview
-  `#3195 <http://code.osuosl.org/issues/3195>`_ **Feature** Add links to editing permissions
   on Group-Permissions page
-  `#3207 <http://code.osuosl.org/issues/3207>`_ **Bug** Ram/Disk is missing jquery progress
   bar on resources tab for user and group
-  `#3231 <http://code.osuosl.org/issues/3231>`_ **Feature** Separate the create VM javascript
   code and CSS from template into their own files
-  `#3261 <http://code.osuosl.org/issues/3261>`_ **Feature** Create sendable disabled
   dropdowns
-  `#3267 <http://code.osuosl.org/issues/3267>`_ **Bug** Adding a cluster with a bogus
   hostname results in a django exception page
-  `#3279 <http://code.osuosl.org/issues/3279>`_ **Feature** Cluster: Add totals to detail
   page
-  `#3291 <http://code.osuosl.org/issues/3291>`_ **Feature** VM Edit: add more parameters
-  `#3297 <http://code.osuosl.org/issues/3297>`_ **Feature** VM: Improve detail page
-  `#3321 <http://code.osuosl.org/issues/3321>`_ **Feature** Jobs: link to job output on
   overview page
-  `#3351 <http://code.osuosl.org/issues/3351>`_ **Bug** Create VM: Don't show a secondary
   node if drbd selected for disk template and there's only one node
   available
-  `#3393 <http://code.osuosl.org/issues/3393>`_ **Bug** Getting 500 internal sever error on
   VM reboot
-  `#3405 <http://code.osuosl.org/issues/3405>`_ **Bug** CSRF Vulnerabilities in AJAX POST
   requests that do not use forms.
-  `#3453 <http://code.osuosl.org/issues/3453>`_ **Bug** Clearing job error did not clear it
   from the objects detail page
-  `#3459 <http://code.osuosl.org/issues/3459>`_ **Feature** Ability to clear job error from
   detail page
-  `#3477 <http://code.osuosl.org/issues/3477>`_ **Bug** SSH keys: strip new lines
-  `#3495 <http://code.osuosl.org/issues/3495>`_ **Bug** javascript on vm create page is
   reseting node selection and hostname
-  `#3501 <http://code.osuosl.org/issues/3501>`_ **Bug** Nodes column empty on clusters page
-  `#3507 <http://code.osuosl.org/issues/3507>`_ **Feature** Add units, better description to
   Node detail page
-  `#3543 <http://code.osuosl.org/issues/3543>`_ **Bug** A failed create VM will list two jobs
-  `#3633 <http://code.osuosl.org/issues/3633>`_ **Feature** Rename "reboot" button on modify
   page
-  `#999 <http://code.osuosl.org/issues/999>`_ **Feature** VM Creation: add network boot
   support
-  `#3111 <http://code.osuosl.org/issues/3111>`_ **Bug** overview page css for tables is not
   correct
-  `#3201 <http://code.osuosl.org/issues/3201>`_ **Bug** Setting owner without cluster write
   access
-  `#3339 <http://code.osuosl.org/issues/3339>`_ **Bug** Virtual Machine Template - Model
   Field Names Update
-  `#3345 <http://code.osuosl.org/issues/3345>`_ **Bug** Virtual Machine Action Buttons not
   Fully Disabled
-  `#3363 <http://code.osuosl.org/issues/3363>`_ **Bug** Node Bar Discrepencies
-  `#3369 <http://code.osuosl.org/issues/3369>`_ **Feature** Job list: Update icons for node,
   cluster, and vm
-  `#3375 <http://code.osuosl.org/issues/3375>`_ **Feature** update object log templates to
   include link to the associated job when appropriate

v0.5
----

Notable Changes:
^^^^^^^^^^^^^^^^

-  Status Dashboard is now the front page for GWM

   -  lists cluster status for admins.
   -  lists summary of virtual machines status for users.
   -  lists resource usage for the user and groups.
   -  error list including job failures and ganeti errors.

-  Integrated NoVNC, an HTML5 + WebSockets VNC viewer
-  Super users can now view resource usage and permissions for users and
   groups.
-  Virtual machine lists are now paginated for quicker loading
-  Ram and CPU quota is now based off running virtual machines
-  Improved layout
-  Virtual Machines list now properly works for cluster admins

Tickets
^^^^^^^

-  `#273 <http://code.osuosl.org/issues/273>`_ **Bug** Deleting a User/Group from a Cluster
   does not remove custom Quota
-  `#399 <http://code.osuosl.org/issues/399>`_ **Bug** Cluster admin permission does not
   extend permissions to virtual machines
-  `#537 <http://code.osuosl.org/issues/537>`_ **Feature** Need final layout for index page
-  `#561 <http://code.osuosl.org/issues/561>`_ **Feature** Implement a common logging system
-  `#585 <http://code.osuosl.org/issues/585>`_ **Feature** Logging - Group edit
-  `#591 <http://code.osuosl.org/issues/591>`_ **Feature** Logging - core tables
-  `#597 <http://code.osuosl.org/issues/597>`_ **Feature** Implement pagination and or
   incremental loading for Cluster Detail > Virtual Machines
-  `#609 <http://code.osuosl.org/issues/609>`_ **Feature** Cluster should only automatically
   import virtual machines once
-  `#693 <http://code.osuosl.org/issues/693>`_ **Bug** Clean up VM config page
-  `#729 <http://code.osuosl.org/issues/729>`_ **Feature** Add sorting capability on VM/Node
   pages
-  `#765 <http://code.osuosl.org/issues/765>`_ **Feature** Add ability to reinstall an
   existing VM
-  `#849 <http://code.osuosl.org/issues/849>`_ **Bug** Create a Ganeti Web Manager logo
-  `#903 <http://code.osuosl.org/issues/903>`_ **Feature** Virtual Machine Creation - Manually
   setting of nic\_type
-  `#909 <http://code.osuosl.org/issues/909>`_ **Feature** Virtual Machine Creation -
   Auto-Start
-  `#963 <http://code.osuosl.org/issues/963>`_ **Bug** Virtual Machine Creation - Formatting
   on Legend Fields
-  `#1017 <http://code.osuosl.org/issues/1017>`_ **Feature** Admin VM pages: show cluster each
   VM is in
-  `#1023 <http://code.osuosl.org/issues/1023>`_ **Bug** Cluster Removal: no progress shown
-  `#1029 <http://code.osuosl.org/issues/1029>`_ **Bug** Orphan VM: order VMs
-  `#1035 <http://code.osuosl.org/issues/1035>`_ **Feature** VM Creation: allow units for
   memory/disk
-  `#1041 <http://code.osuosl.org/issues/1041>`_ **Bug** VM VNC: keep console connected when
   switching tabs
-  `#1779 <http://code.osuosl.org/issues/1779>`_ **Feature** Improve usability of User
   create/edit form
-  `#1917 <http://code.osuosl.org/issues/1917>`_ **Bug** Changing Tab disconnects VNC
-  `#1935 <http://code.osuosl.org/issues/1935>`_ **Feature** Implement HTML5 based VNC console
   using noVNC
-  `#1947 <http://code.osuosl.org/issues/1947>`_ **Feature** edit and delete buttons on
   cluster list page should have a title
-  `#1959 <http://code.osuosl.org/issues/1959>`_ **Feature** Add "power" buttons on VNC page
-  `#1965 <http://code.osuosl.org/issues/1965>`_ **Bug** Cluster edit/create form doesn't need
   to confirm password entered
-  `#2025 <http://code.osuosl.org/issues/2025>`_ **Bug** Sorting needs to be numeric
-  `#2037 <http://code.osuosl.org/issues/2037>`_ **Feature** Add sortable columns on Cluster
   view
-  `#2055 <http://code.osuosl.org/issues/2055>`_ **Feature** Swap slug with cluster
   description on clusters view
-  `#2061 <http://code.osuosl.org/issues/2061>`_ **Bug** Edit cluster always requires password
-  `#2067 <http://code.osuosl.org/issues/2067>`_ **Bug** Display units for quota
-  `#2163 <http://code.osuosl.org/issues/2163>`_ **Feature** activation page needs to include
   more information
-  `#2169 <http://code.osuosl.org/issues/2169>`_ **Feature** VM Reboot and Shutdown buttons
   should require confirmation
-  `#2175 <http://code.osuosl.org/issues/2175>`_ **Feature** RAM/CPU Quota should be based off
   running virtualmachines
-  `#2181 <http://code.osuosl.org/issues/2181>`_ **Feature** add auto create for profile and
   organizations
-  `#2187 <http://code.osuosl.org/issues/2187>`_ **Bug** Profile changes need "success"
   message
-  `#2193 <http://code.osuosl.org/issues/2193>`_ **Bug** VM Creation (/vm/add): Hide options
   with only one choice
-  `#2259 <http://code.osuosl.org/issues/2259>`_ **Bug** fix issues with vncauthproxy
-  `#2301 <http://code.osuosl.org/issues/2301>`_ **Bug** Create a daemon capable of managing
   multiple websockets
-  `#2307 <http://code.osuosl.org/issues/2307>`_ **Feature** add NoVNC to the UI
-  `#2313 <http://code.osuosl.org/issues/2313>`_ **Feature** fix spacing on registration email
   confirm page
-  `#2319 <http://code.osuosl.org/issues/2319>`_ **Bug** account activated screen should have
   a link that takes you to the login page
-  `#2331 <http://code.osuosl.org/issues/2331>`_ **Bug** RAPI error on cluster list page shows
   error icon to the right of the cluster name
-  `#2367 <http://code.osuosl.org/issues/2367>`_ **Bug** VNC server access w/ or w/o proxy
-  `#2373 <http://code.osuosl.org/issues/2373>`_ **Feature** Setting: Use noVNC or Java VNC
   jar
-  `#2379 <http://code.osuosl.org/issues/2379>`_ **Feature** VNC server may only listen on
   localhost on the node
-  `#2385 <http://code.osuosl.org/issues/2385>`_ **Bug** Update setup\_vnc\_forwarding
-  `#2391 <http://code.osuosl.org/issues/2391>`_ **Bug** Nodes tab stops working when node is
   marked as offline
-  `#2397 <http://code.osuosl.org/issues/2397>`_ **Feature** Make vncauthproxy work with INET
   socket and JSON requests
-  `#2409 <http://code.osuosl.org/issues/2409>`_ **Feature** Store ganeti errors
-  `#2451 <http://code.osuosl.org/issues/2451>`_ **Feature** Registration/Login Templates need
   to be reworked
-  `#2511 <http://code.osuosl.org/issues/2511>`_ **Bug** VM Creation: NIC link should always
   be present
-  `#2523 <http://code.osuosl.org/issues/2523>`_ **Bug** ClusterUser.used\_resources is
   reporting total resources used across all clusters
-  `#2529 <http://code.osuosl.org/issues/2529>`_ **Feature** Display correct op for VM job
   status
-  `#2541 <http://code.osuosl.org/issues/2541>`_ **Bug** RAPI error icon on list pages is not
   aligned with other icons
-  `#2547 <http://code.osuosl.org/issues/2547>`_ **Feature** Show progress icon when loading
   VM table data (pagination)
-  `#2553 <http://code.osuosl.org/issues/2553>`_ **Bug** ClusterUser.clusters should be
   removed
-  `#2559 <http://code.osuosl.org/issues/2559>`_ **Feature** improve css for pagination links
-  `#2565 <http://code.osuosl.org/issues/2565>`_ **Bug** used resources should be based on
   ownership, not permissions
-  `#2571 <http://code.osuosl.org/issues/2571>`_ **Bug** fix used\_resources to use aggregate
   functions
-  `#2577 <http://code.osuosl.org/issues/2577>`_ **Bug** quota check while creating VMs is
   performign two calls to ClusterUser.used\_resources
-  `#2583 <http://code.osuosl.org/issues/2583>`_ **Bug** ClusterUser.used\_resources is using
   an extra query to determine owner
-  `#2589 <http://code.osuosl.org/issues/2589>`_ **Bug** ClusterUser.used\_resources should
   return 0 instead of None when no resources are used
-  `#2595 <http://code.osuosl.org/issues/2595>`_ **Bug** Virtual machines list is showing no
   virtual machines for superuser
-  `#2601 <http://code.osuosl.org/issues/2601>`_ **Bug** Cluster virtual machine list is not
   sorted by cluster after pagination
-  `#2607 <http://code.osuosl.org/issues/2607>`_ **Bug** update sorting to work with
   pagination
-  `#2613 <http://code.osuosl.org/issues/2613>`_ **Bug** Overview Page Not Correctly Loading
   Cluster
-  `#2619 <http://code.osuosl.org/issues/2619>`_ **Bug** time.sleep() is dangerous
-  `#2625 <http://code.osuosl.org/issues/2625>`_ **Bug** Virtual machine creation form JS
   shouldn't be a jQuery plugin
-  `#2649 <http://code.osuosl.org/issues/2649>`_ **Feature** update permission edits to use
   signals for logging
-  `#2781 <http://code.osuosl.org/issues/2781>`_ **Bug** VM User list not formatted correctly
-  `#2787 <http://code.osuosl.org/issues/2787>`_ **Feature** Link to cluster from VM page
-  `#2793 <http://code.osuosl.org/issues/2793>`_ **Bug** VM owner needs to be shown somewhere
-  `#2799 <http://code.osuosl.org/issues/2799>`_ **Bug** Adding non-admin or admin user as
   owner causes error
-  `#2805 <http://code.osuosl.org/issues/2805>`_ **Feature** Improve VM pagination
-  `#2811 <http://code.osuosl.org/issues/2811>`_ **Feature** logging - log group permissions
   editing
-  `#2847 <http://code.osuosl.org/issues/2847>`_ **Feature** deleted VM cleanup
-  `#2859 <http://code.osuosl.org/issues/2859>`_ **Bug** overview - if used resources are zero
   then progresbar throws an exception
-  `#2865 <http://code.osuosl.org/issues/2865>`_ **Feature** Add caching for admin tasks on
   overview page
-  `#2871 <http://code.osuosl.org/issues/2871>`_ **Bug** Fix disk usage bar alignment
-  `#2877 <http://code.osuosl.org/issues/2877>`_ **Feature** Ganeti Error 401 should not be
   recorded for the VM
-  `#2883 <http://code.osuosl.org/issues/2883>`_ **Feature** Ganeti Error 404 for cluster
   should not be recorded for VMs
-  `#2889 <http://code.osuosl.org/issues/2889>`_ **Feature** Add South migration and
   instructions for 0.4 => 0.5
-  `#2895 <http://code.osuosl.org/issues/2895>`_ **Bug** Tell user on overview page if they
   don't have access to anything
-  `#2907 <http://code.osuosl.org/issues/2907>`_ **Bug** VM power permission should display
   console
-  `#2913 <http://code.osuosl.org/issues/2913>`_ **Bug** Overview: Cluster link doesn't show
   the name and has incorrect hyperlink
-  `#2919 <http://code.osuosl.org/issues/2919>`_ **Bug** fix css for novnc page
-  `#2925 <http://code.osuosl.org/issues/2925>`_ **Feature** allow users to switch between
   personas for resource usage summary
-  `#2943 <http://code.osuosl.org/issues/2943>`_ **Bug** startup, shutdown, delete buttons on
   console page don't work
-  `#2949 <http://code.osuosl.org/issues/2949>`_ **Feature** Include ganeti install hook for
   sshkeys.py
-  `#2961 <http://code.osuosl.org/issues/2961>`_ **Feature** show all permissions on user page
-  `#2991 <http://code.osuosl.org/issues/2991>`_ **Bug** Annotate and/or aggregate complains
   on postgres backend
-  `#2997 <http://code.osuosl.org/issues/2997>`_ **Bug** Deleting VM always "in progress"
-  `#3003 <http://code.osuosl.org/issues/3003>`_ **Bug** Showing errors when they aren't
   errors
-  `#3009 <http://code.osuosl.org/issues/3009>`_ **Feature** Add job ID's to overview
-  `#3021 <http://code.osuosl.org/issues/3021>`_ **Bug** CreateVM: IAllocator Checkbox
-  `#3063 <http://code.osuosl.org/issues/3063>`_ **Bug** Confirmation box has improper
   formatting
-  `#3069 <http://code.osuosl.org/issues/3069>`_ **Feature** Include documentation on how to
   setup SMTP

v0.4
----

Initial Release

-  Caching system
-  Permissions system:

   -  user & group management
   -  per cluster/vm permissions

-  basic VM management: Create, Delete, Start, Stop, Reboot
-  ssh key feed
-  basic quota system
-  Import tools
