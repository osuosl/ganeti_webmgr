from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.utils.translation import ugettext as _
from django.utils import simplejson as json
from object_permissions import get_users_any
from django.db.models import Q

from .models import SSHKey
from clusters.models import Cluster
from virtualmachines.models import VirtualMachine


def ssh_keys(request, api_key):
    """ Lists all keys for all clusters managed by GWM """
    """
    Show all ssh keys which belong to users, who have any perms on the cluster
    """
    if settings.WEB_MGR_API_KEY != api_key:
        return HttpResponseForbidden(_("You're not allowed to view keys."))

    users = set()
    for cluster in Cluster.objects.all():
        users = users.union(set(get_users_any(cluster)
                                .values_list("id", flat=True)))
    for vm in VirtualMachine.objects.all():
        users = users.union(set(get_users_any(vm)
                                .values_list('id', flat=True)))

    keys = SSHKey.objects \
        .filter(Q(user__in=users) | Q(user__is_superuser=True)) \
        .values_list('key', 'user__username')\
        .order_by('user__username')

    keys_list = list(keys)
    return HttpResponse(json.dumps(keys_list), mimetype="application/json")
