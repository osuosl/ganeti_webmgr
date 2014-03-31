.. _process:

Development Process
===================
.. todo::
	link to cycle, versions
	link to dev guide


Issue Triage
------------

When an issue is reported on code.osuosl.org, the core team will triage the issue, assigning it to a release version, rejecting it, or sending it back for more information. This process may take place as part of planning for a new version release, or ad hoc in order to address an important bug in the current release.

Features
~~~~~~~~

Features will be considered only for the next minor or major version release. If the current release cycle has not yet reached the 'feature freeze' deadline, the feature may be considered for the current release; otherwise it should be assigned to a future release.

Enhancements
~~~~~~~~~~~~

Enhancements will not be considered for the current version after that version's feature freeze date. Enhancement issues must apply to a current existing feature, if they introduce new basic functionality, they should be reclassified as Features. If they address malfunctioning code or incorrect functionality, they should be reclassified as Bugs.

Bugs
~~~~

Bugs may be assigned to a release at any time. If they apply to an existing released version, either a new point release must be created, or the bug must be incorporated into the next major or minor release. For example, an urgent fix to the 0.10.1 release should generate a 0.10.2 release to contain the changes. A less urgent fix for 0.10.1 might simply be incorporated into 0.11. In general, we try to collect multiple fixes into any point or minor release.


Workflow
--------

The following workflow should be followed when contributing code.

Assignment
~~~~~~~~~~

Issues are assigned to developers in several ways:

- direct assignment by the project lead
- volunteer self-assignment
  
The project lead and core developers may re-assign issues based on time or other considerations.


Branching
~~~~~~~~~

The git branching model essentially follows the git-flow model. 

.. todo::
	git-flow details

When work begins on an issue, a new branch should be created containing the issue type and number. 

::

	git checkout -b feature/12345

This branch should be based on the main branch to which it will apply. For features and enhancements, this should always be develop. For bugs that apply to a specific release, the branch may be taken from that release's branch.


Commit Messages
~~~~~~~~~~~~~~~

Commit messages should be informative, they should contain everything another developer might need to know in order to understand your commit. It should contain the problem addressed by the commit and a quick description of the solution. 

Commit messages have a header line and a body, the header line should contain a very brief description of the commit, and should be limited to 50 characters. The body should contain a bit more detail on what was changed. 
	  
In order to track the commit within our bug tracker, the commit message should also contain a reference to the issue number:

::

	refs: #12345

An example commit:

::

	Short (50 chars or less) summary of changes

	refs: #12345

	More detailed explanatory text, if necessary.  Wrap it to about 72
	characters or so. In some contexts, the first line is treated as the
	subject of an email and the rest of the text as the body.  The blank
	line separating the summary from the body is critical (unless you omit
	the body entirely); some git tools can get confused if you run the
	two together.

	Further paragraphs come after blank lines.

 	 - Bullet points are okay, too

 	 - Typically a hyphen or asterisk is used for the bullet, preceded by a
   	single space, with blank lines in between, but conventions vary
   	here

	# Please enter the commit message for your changes. Lines starting
	# with '#' will be ignored, and an empty message aborts the commit.
	# On branch master
	# Changes to be committed:
	#   (use "git reset HEAD <file>..." to unstage)
	#
	# modified:   hello.py
	#


Review
~~~~~~

Before being merged into develop or a release branch, all work must be reviewed. Our process is informal. A developer may ask another developer to review their work, or a project lead may assign issues for review. To assign someone to review an issue, the issue should be assigned to the reviewer with the status "needs review".

Code, documentation and internationalization should all be reviewed before being merged.

**Code review criteria**

- code should be examined for logical or typographical errors
- code should be examined in the context of the larger application
	- does the code fit the structure of the application?
	- does the code follow the application's conventions, such as method names, variable namespaces, etc?
	- does the code leverage existing methods, or re-implement things that exist elsewhere?
- code should be audited for standards compliance (i.e. PEP8)
- unit tests should be run in a local dev environment to verify there are no failures
- the features the code effects should be tested by running the application and using those features

  
Internationalization should be reviewed as code. If the accuracy of translations cannot be confirmed, the code should be reviewed to ensure the correct strings are translated and no errors have been introduced by adding translations to strings.

**Documentation review criteria**

- documentation should be examined for misspellings, typographical errors and grammar
- documentation should be examined for formatting consistency
	- are headers, paragraphs and other elements used consistently with other docs?
	- is the narrative style and organization consistent with other docs?
- documentation should be complete, and where it is not, 'todo' blocks should be included with descriptions of what is still pending
- documentation should be accurate - docs containing instructions should be tested by following those instructions and verifying that the produce the correct result

  
If the work passes review, the reviewer should add a note to the issue in the tracker, describing what was tested and verifying that the work passed. 

If the work does not pass review, the reviewer should add a note in the tracker describing the problem and describing the necessary fixes if known. The reviewer will then re-assign the issue back to the original developer with the status "needs work".

In some cases, work might pass the review, but contain small things that could be cleaned up or done more efficiently. If time constraints or other factors make reassigning for more work undesirable, a detailed note should be added to the issue describing things that could be done to improve the code.


Merging
~~~~~~~

When work has passed review, the project lead, or a developer assigned by the lead, may merge the work into the appropriate branch. 

If the branch has diverged significantly from its parent, the parent should be merged with the branch prior to submitting for review. If this has not been done, the developer responsible for merging into the parent branch may do this, or may assign it back to the original developer. If significant conflicts arise during merging, the issue should be reassigned to the original developer to resolve the conflicts. 

Merging should be done with the --no-ff flag to preserve commit history.

After merging the parent branch into the submitted issue, the merging developer will run all tests for the project to ensure no bugs have been introduced by the merge. 

When all tests pass, the work will be merged with the parent branch. After merging, the developer doing the merge will run the test suit again.

If all tests pass, the developer will update the issue in the tracker, adding a note that the code was merged and any comments on conflicts resolved. The developer will then change the status of the issue to "resolved".


Github and Pull Requests
------------------------

If work is done on GitHub or on an external repository rather than the OSL Gitolite instance, the work will be submitted to the core via a Github pull request. 

Pull requests will be subject to the same review process outlined above, and should correspond to an issue in the OSL issue tracker. If no such issue exists, it must be created before accepting the pull request. When the pull request is approved, a new branch will be created following the normal naming conventions, and the work pulled into this branch. From this point, the work follows the same workflow as above.

If the original developer does not have or is not willing to create an account on the OSL tracker, and the issue needs to be assigned back for additional work, such assignment may be communicated via email, an issue on the Github issue tracker for the developers' clone. If the developer is not willing to participate in this process, a core developer may be assigned to adopt the work, and the issue will be assigned to that developer for further work.