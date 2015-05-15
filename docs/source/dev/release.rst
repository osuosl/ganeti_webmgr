.. _release:

===================
GWM Release Process
===================

The Ganeti Web Manager release process involves several stages of testing and preparation.

*Feature Freeze*
    All of the features to be included in this release are complete - no new feature issues can be created for this release, and all remaining issues should be resolved.
*Release Branch*
    When all issues are resolved, a new release branch is created to contain the new release, it will be named for the version, i.e. release/0.10.2. The version number strings in this branch will be updated to the correct version number.
*First Test Phase*
    The release branch version of GWM will be tested on the OSL GWM staging server. The deployment and all new features for this version should be tested, and the unit test suite will be run.
*Documentation Audit*
    While testing on the staging server, the documentation will be audited to make sure it is up to date and correct for this version. Any issues will be filed as bugs against this version.
*First Bug Fix Phase*
    Any code or documentation bugs discovered through testing on the staging server will be addressed during this time, and fixes applied to the release branch. If no bugs are found, we move on to the next phase.
*First Release Candidate* (two weeks)
    A release canidate tag is created from the release branch, and announced on the mailing list and in IRC. The release candidate is deployed on staging for continued testing. The release candidate will be tested at OSL and by end users for two weeks. Any bugs discovered will be filed against this version.
*Second Bug Fix Phase*
    If bugs were found in the release candidate during the two week testing period, fixes should be applied to the release branch as soon as possible. If no bugs were found, the release moves on to the Final Release step.
*Second Release Candidate*
    If bugs were fixed in the first release candidate, a new candidate tag is created and is tested for one week. Further release candidates may be created as needed to fix bugs, each release candidate should have a lifetime of one week.
*Final Release*
    If no issues were found in the last release candidate after the one or two week testing phase, the release is considered final, a release tag is created. See below for full list of Final Release tasks.

Final Release Tasks
-------------------

Creating a final release consists of the following tasks.

1. All issues for the release version should be resolved and closed
2. Bump version in docs/source/conf.py and in ganeti_webmgr/constants.py
3. Create a release tag for this version, e.g. 0.10.2
4. Create a tar file for this release and upload it to https://code.osuosl.org/projects/ganeti-webmgr/files
5. Create a Python package from the tag
6. Announce the new release to the mailing list and IRC channels
