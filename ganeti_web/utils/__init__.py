import random
import string

from django.conf import settings

from clusters.models import Cluster

from .client import GanetiRapiClient


def generate_random_password(length=12):
    "Generate random sequence of specified length"
    return "".join(random.sample(string.letters + string.digits, length))


RAPI_CACHE = {}
RAPI_CACHE_HASHES = {}


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
    rapi = GanetiRapiClient(host, port, user, password,
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
