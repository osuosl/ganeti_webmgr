import random
import string
from collections import defaultdict

from django.conf import settings

from .client import GanetiRapiClient, GanetiApiError
from .proxy import RapiProxy, XenRapiProxy

from ganeti_webmgr.ganeti_web import constants
from ganeti_webmgr.ganeti_web.caps import has_balloonmem


def generate_random_password(length=12):
    "Generate random sequence of specified length"
    return "".join(random.sample(string.letters + string.digits, length))


RAPI_CACHE = {}
RAPI_CACHE_HASHES = {}


def get_rapi_client():
    """
    This function returns Rapi client based on current circumstances.
    I decided to make this function separate so that we can easily patch it in
    tests.
    """
    # If the tests are running, we replace GanetiRapiClient with its
    # descendant, RapiProxy.  This is due to the fact, that explicit replacing
    # in tests
    #     client.GanetiRapiClient = RapiProxy
    # doesn't work anymore.  Additional advantage is about 3 lines lesser files
    # containing tests.
    rapi_client = GanetiRapiClient
    if settings.TESTING:
        rapi_client = RapiProxy
    return rapi_client


def get_rapi(hash, cluster):
    """
    Retrieves the cached Ganeti RAPI client for a given hash.  The Hash is
    derived from the connection credentials required for a cluster.  If the
    client is not yet cached, it will be created and added.

    If a hash does not correspond to any cluster then Cluster.DoesNotExist will
    be raised.

    @param cluster - either a cluster object, or ID of object.  This is used
    for resolving the cluster if the client is not already found.  The id is
    used rather than the hash, because the hash is mutable.

    @return a Ganeti RAPI client.
    """
    # preventing circular imports
    from ganeti_webmgr.clusters.models import Cluster

    rapi_client = get_rapi_client()

    if hash in RAPI_CACHE:
        return RAPI_CACHE[hash]

    # always look up the instance, even if we were given a Cluster instance
    # it ensures we are retrieving the latest credentials.  This helps avoid
    # stale credentials.  Retrieve only the values because we don't actually
    # need another Cluster instance here.
    if isinstance(cluster, (Cluster,)):
        cluster = cluster.id
    (credentials,) = Cluster.objects.filter(id=cluster) \
        .values_list('hash', 'hostname', 'port', 'username', 'password')
    hash, host, port, user, password = credentials
    user = user or None
    # decrypt password
    # XXX django-fields only stores str, convert to None if needed
    password = Cluster.decrypt_password(password) if password else None
    password = None if password in ('None', '') else password

    # now that we know hash is fresh, check cache again. The original hash
    # could have been stale. This avoids constructing a new RAPI that already
    # exists.
    if hash in RAPI_CACHE:
        return RAPI_CACHE[hash]

    # delete any old version of the client that was cached.
    if cluster in RAPI_CACHE_HASHES:
        del RAPI_CACHE[RAPI_CACHE_HASHES[cluster]]

    # Set connect timeout in settings.py so that you do not learn patience.
    rapi = rapi_client(host, port, user, password,
                       timeout=settings.RAPI_CONNECT_TIMEOUT)
    RAPI_CACHE[hash] = rapi
    RAPI_CACHE_HASHES[cluster] = hash
    return rapi


def clear_rapi_cache():
    """
    clears the rapi cache
    """
    RAPI_CACHE.clear()
    RAPI_CACHE_HASHES.clear()


def cluster_default_info(cluster, hypervisor=None):
    """
    Returns a dictionary containing the following
    default values set on a cluster:
        iallocator, hypervisors, vcpus, ram, nictype,
        nicmode, kernelpath, rootpath, serialconsole,
        bootorder, imagepath
    """
    # Create variables so that dictionary lookups are not so horrendous.
    info = cluster.info
    beparams = info['beparams']['default']
    hvs = info['enabled_hypervisors']

    if hypervisor is not None:
        if hypervisor not in hvs:
            raise RuntimeError("Was asked to deal with a cluster/HV mismatch")
        else:
            hv = hypervisor
    else:
        hv = info['default_hypervisor']

    hvparams = info['hvparams'][hv]
    if hv == 'kvm':
        c = constants.KVM_CHOICES
    elif hv == 'xen-hvm' or hv == 'xen-pvm':
        c = constants.HVM_CHOICES
        if hv == 'xen-pvm':
            # PVM does not have disk types or nic types, so these options get
            # taken from HVM. This does not affect forms as pvm ignores
            # the disk_type and nic_type fields.
            hvparams['disk_type'] = info['hvparams']['xen-hvm']['disk_type']
            hvparams['nic_type'] = info['hvparams']['xen-hvm']['nic_type']
    else:
        c = constants.NO_CHOICES

    disktypes = c['disk_type']
    nictypes = c['nic_type']
    bootdevices = c['boot_order']

    try:
        iallocator_info = info['default_iallocator']
    except:
        iallocator_info = None

    if 'nicparams' in info:
        nic_mode = info['nicparams']['default']['mode']
        nic_link = info['nicparams']['default']['link']
    else:
        nic_mode = None
        nic_link = None

    extraparams = {
        'boot_devices': bootdevices,
        'disk_types': disktypes,
        'hypervisor': hv,
        'hypervisors': zip(hvs, hvs),
        'iallocator': iallocator_info,
        'nic_types': nictypes,
        'nic_mode': nic_mode,
        'nic_link': nic_link,
        'vcpus': beparams['vcpus'],
    }

    if has_balloonmem(cluster):
        extraparams['memory'] = beparams['maxmem']
    else:
        extraparams['memory'] = beparams['memory']

    return dict(hvparams, **extraparams)


def hv_prettify(hv):
    """
    Prettify a hypervisor name, if we know about it.
    """

    prettified = {
        "kvm": "KVM",
        "lxc": "Linux Containers (LXC)",
        "xen-hvm": "Xen (HVM)",
        "xen-pvm": "Xen (PVM)",
    }

    return prettified.get(hv, hv)


def cluster_os_list(cluster):
    """
    Create a detailed manifest of available operating systems on the cluster.
    """
    try:
        return os_prettify(cluster.rapi.GetOperatingSystems())
    except GanetiApiError:
        return []


def os_prettify(oses):
    """
    Pretty-print and format a list of operating systems.

    The actual format is a list of tuples of tuples. The first entry in the
    outer tuple is a label, and then each successive entry is a tuple of the
    actual Ganeti OS name, and a prettified display name. For example:

    [
        ("Image",
            ("image+obonto-hungry-hydralisk", "Obonto Hungry Hydralisk"),
            ("image+fodoro-core", "Fodoro Core"),
        ),
        ("Dobootstrop",
            ("dobootstrop+dobion-lotso", "Dobion Lotso"),
        ),
    ]
    """

    # In order to convince Django to make optgroups, we need to nest our
    # iterables two-deep. (("header", ("value, "label"), ("value", "label")))
    # http://docs.djangoproject.com/en/dev/ref/models/fields/#choices
    # We do this by making a dict of lists.
    d = defaultdict(list)

    for name in oses:
        try:
            # Split into type and flavor.
            t, flavor = name.split("+", 1)
            # Prettify flavors. "this-boring-string" becomes
            #"This Boring String"
            flavor = " ".join(word.capitalize() for word in flavor.split("-"))
            d[t.capitalize()].append((name, flavor))
        except ValueError:
            d["Unknown"].append((name, name))

    l = d.items()
    l.sort()

    return l


def compare(x, y):
    """
    Using the python cmp function, returns a string detailing the change in
        difference
    """
    i = cmp(x, y)
    if y is None and i != 0:
        return "removed"
    if isinstance(x, basestring) and i != 0:
        if x == "":
            return "set to %s" % (y)
        elif y == "":
            return "removed"
        return "changed from %s to %s" % (x, y)
    elif isinstance(x, bool) and i != 0:
        if y:
            return "enabled"
        else:
            return "disabled"
    if i == -1:
        return "increased from %s to %s" % (x, y)
    elif i == 1:
        return "decreased from %s to %s" % (x, y)
    else:
        return ""


def contains(e, t):
    """
    Determine whether or not the element e is contained within
    the list of tuples t
    """
    return any(e == v[0] for v in t)


def get_hypervisor(vm):
    """
    Given a VirtualMachine object,
    return its hypervisor depending on what hvparam fields
    it contains.
    """
    if vm.info:
        info = vm.info['hvparams']
        if 'serial_console' in info:
            return 'kvm'
        elif 'initrd_path' in info:
            return 'xen-pvm'
        elif 'acpi' in info:
            return 'xen-hvm'
    return None
