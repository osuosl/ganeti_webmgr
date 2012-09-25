"""
Capabilities for clusters.

This module can classify clusters into a capability group, and provides some
helpful utility functions for determining what clusters are capable of doing.

Versions recognized by this module (and GWM at large):

 * ANCIENT: Ganeti from before the dawn of time. Ganeti 2.1 and earlier, as
   well as any unrecognized versions.
 * GANETI22: Ganeti 2.2.x
 * GANETI23: Ganeti 2.3.x
 * GANETI24: Ganeti 2.4.x prior to 2.4.2
 * GANETI242: Ganeti 2.4.2 and newer in the 2.4.x series
 * GANETI25: Ganeti 2.5.x
 * FUTURE: Ganeti which probably is newer than, and somewhat
   backwards-compatible with, the newest version of Ganeti which GWM
   officially supports.

Note that all bets are off if the cluster's version doesn't correspond to the
x.y.z (major.minor.patch) versioning pattern.
"""

ANCIENT, GANETI22, GANETI23, GANETI24, GANETI242, GANETI25, GANETI26, FUTURE = range(8)

def classify(cluster):
    """
    Determine the class of a cluster by examining its version.
    """

    # Extract the version string from the cluster.
    s = cluster.info["software_version"]

    # First, try the whole splitting thing. If we can't do it that way, assume
    # it's ancient.
    try:
        version = tuple(int(x) for x in s.split("."))
    except ValueError:
        return ANCIENT

    if version >= (2, 6, 1):
        return FUTURE
    if version >= (2, 6, 0):
        return GANETI26
    elif version >= (2, 5, 0):
        return GANETI25
    elif version >= (2, 4, 2):
        return GANETI242
    elif version >= (2, 4, 0):
        return GANETI24
    elif version >= (2, 3, 0):
        return GANETI23
    elif version >= (2, 2, 0):
        return GANETI22
    else:
        return ANCIENT


def has_shutdown_timeout(cluster):
    """
    Determine whether a cluster supports timeouts for shutting down VMs.
    """

    return classify(cluster) >= GANETI25


def has_cdrom2(cluster):
    """
    Determine whether a cluster supports a second CDROM device.
    """

    return classify(cluster) >= GANETI242

def req_maxmem(cluster):
    """
    Determine whether a cluster requires min/maxmem rather than
    just memory.
    """

    return classify(cluster) >= GANETI26
