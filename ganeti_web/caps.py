"""
Capabilities for clusters.

This module can classify clusters into a capability group, and provides some
helpful utility functions for determining what clusters are capable of doing.

Versions recognized by this module (and GWM at large):

 * ANCIENT: Ganeti from before the dawn of time. Ganeti 2.2 and earlier, as
   well as any unrecognized versions.
 * GANETI23: Ganeti 2.3.x
 * GANETI24: Ganeti 2.4.x
 * GANETI25: Ganeti 2.5.x
 * FUTURE: Ganeti which probably is newer than, and somewhat
   backwards-compatible with, the newest version of Ganeti which GWM
   officially supports.

Note that all bets are off if the cluster's version doesn't correspond to the
x.y.z (major.minor.patch) versioning pattern.
"""

ANCIENT, GANETI22, GANETI23, GANETI24, GANETI25, FUTURE = range(6)

def classify(cluster):
    """
    Determine the class of a cluster by examining its version.
    """

    # Extract the version string from the cluster.
    s = cluster.info["software_version"]

    # First, try the whole splitting thing. If we can't do it that way, assume
    # it's ancient.
    try:
        major, minor, patch = [int(x) for x in s.split(".")]
    except ValueError:
        return ANCIENT

    version = major, minor

    if version < (2, 2):
        return ANCIENT
    elif version > (2, 5):
        return FUTURE
    elif minor == 2:
        return GANETI22
    elif minor == 3:
        return GANETI23
    elif minor == 4:
        return GANETI24
    elif minor == 5:
        return GANETI25

    raise RuntimeError("Impossible condition!")

def has_shutdown_timeout(cluster):
    """
    Determine whether a cluster supports timeouts for shutting down VMs.
    """

    return classify(cluster) >= GANETI25
