.. _release_cycle:

Release Cycle
=============

|gwm| has a feature-based, calendar-influenced release cycle. We aim to release a new minor version roughly twice a year, when new features and bug fixes justify it. 

Versions
--------

|gwm| uses Major.Minor.Point release numbering. Major versions will incorporate major changes to the application and do not gaurantee backwards compatibility with previous major version databases. Minor versions may incorporate significant changes, but must maintain a consistent upgrade path from previous minor versions. Our Major version is currently 0, as we have not yet released version 1.0.0, the current 0.x series will become 1.0.

Our feature target for 1.0 is near complete feature parity with the ganeti RAPI, after which the 1.x series will be considered stable and no further major structural changes will be integrated. We will then begin work on the 2.0.0 development version, which will incorporate major refactoring of the codebase to separate the UI from the core and communications with the RAPI.
