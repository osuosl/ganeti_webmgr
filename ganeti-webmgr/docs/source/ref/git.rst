Working With Git
================

This page holds a list of some helpful git commands. Several of them
were borrowed from Mislav's
`Blog <http://mislav.uniqpath.com/2010/07/git-tips/>`_

**git remote show origin**

    Find out what branches are tracked, configured for pull, configured
    for push, and are 'up to date'.

**git fetch**

    Update local references to remote branches.

**git log -p**

    View each commits changes.

**git log -m -S"search text"**

    Search through commits for commit messages containing the text =
    "search text".

**git reset --soft HEAD**

    Accidentally added the wrong file to the index? This command will
    reset the current head to HEAD and keep your changes.

**git reset --hard HEAD**

    Remove all your changes and reset the current head to HEAD.

**git commit --amend**

    Change the commit message of the most recent commit.

**git add** (**FILENAME** *or* **DIRECTORY**)

    Add a single file or directory to the index. If a directory is
    specified all files that
    are new or have been changed under that directory are added.

**git commit**

    Open up the editor specified by git.editor to review changes and add
    a message.
    If no message is given, then the commit is aborted. Commit takes
    effect once
    the file is written.

**git commit -m "COMMIT MESSAGE"**

    Commit changes with the message "COMMIT MESSAGE".

**git cherry -v BRANCH**

    Will list the commits that are part of the current branch, and not
    part of BRANCH
