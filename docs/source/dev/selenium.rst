Selenium test specs
===================

Since the closest that GWM has to a formal specification seems to be the
bug list, this document is a brainstorm of the behaviors which are
expected of Ganeti Web Manager and can be tested using Selenium. The
specs will be listed here in two categories: Testing that it does what
it should, and testing that it doesn't do what it shouldn't.

*italicized sections aren't specific enough*

When I say that B should happen "immediately" after A, I mean that one
should not have to refresh the page or wait more than a second or two
for B to show up after A occurs. Selenium tests can run really fast, so
it would probably be acceptable (if necessary) to build in a half-second
or so of wait time between A and B, since the succession of events would
still seem "immediate" to a user.

gwm SHOULD:
-----------

User
~~~~

--ANYONE--

-  Create New User: From login page "Not a member" link or (admin only)
   users page Add User button

   -  Display correct error messages for each invalid field in create
      form
   -  Display correct success message when valid form is submitted

--ADMIN--

-  New user appears in user list page accessed from sidebar link

   -  Correct email address is displayed
   -  Correct user creation time displayed
   -  Username links to user detail page

-  Detail page displays correct username, email, join date, active, and
   admin fields
-  New user appears in user list dropdown menu for adding permissions

   -  Edit link leads to edit form pre-populated with user's info

-  Edit form shows correct error when invalid options are entered

   -  Catches mismatched passwords
   -  Forbids changing username to one that's already taken
   -  If 'active' status changed, this change must appear on user detail
      & user list pages
   -  *If superuser status changed, this change must be reflected by
      detail/list pages and in the availability of adding permissions
      from user detail page.*

-  Changes made via user edit form are shown in user list and user
   dropdown lists
-  Remove User link displays popup saying "Remove user: <Username>"
   popup... Clicking "ok" deletes user, "cancel" returns to unaltered
   user list page

--OTHER TESTS RELATED TO USER--

-  Resource usage displayed in tab of detail page should change when
   used resources change
-  When logged in as user, should be able to change own email
   address/password
-  ADMIN should be able to add cluster or add VM to user's permissions
   from tab of detail page, and it should show up in the list
   immediately after being added
-  A test which creates a log (probably done while logged in as user)
   should check that the logged action is displayed correctly in
   the log tab of the user detail page (same with User Actions)

VM:
~~~

These tests should be run after the cluster is added. Ideally the test
cluster will have more than one page of VMs.

-  VM Detail Page shows list of all the VMs that should be there in the
   test cluster

   -  Clicking any heading in the list causes entire list to be sorted
      by that attribute
   -  If >1 page of VMs, number buttons cause correct page of VMs to be
      shown

-  Add VM button on detail page links to same add page as Create VM link
   in sidebar...
-  Owner, Cluster, & other dropdown menus only offer valid options
   (don't allow VM to be created with inactive user as owner?)
-  Help Tip displays text appropriate to box most recently clicked
-  Fails gracefully with bad data

   -  Non-generic error message if invalid DNS name and DNS Name Check
      box was checked

Group
~~~~~

-  Clicking Add Group button on Groups page opens Add Group dialog

   -  Typing a name in the dialog and either hitting enter or clicking
      save creates the group with that name
   -  Group is displayed in group detail page with name as a link to
      group, 0 members, 0 admins.
   -  Edit link on detail page lets you change group's name

      -  New name is reflected in list immediately if you change name
         from edit link

-  Link in groups list takes you to the group detail page

   -  Log tab lists group's creation and the user who created it

-  Users page:

   -  When user added via Add User link,

--OTHER TESTS RELATED TO GROUP--

-  Permissions on cluster/VM
-  Correct display of resource usage

Cluster
~~~~~~~

-  *If cluster is added with no username/password credentials? If quota
   given but no credentials? What should errors be?*

gwm should NOT:
---------------

-  *Show admin things to non-admins*

   -  *Search Results*
   -  access admin-only url by typing the url in, if not logged in as
      admin
   -  *edit user page?*
