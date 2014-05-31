from django.http import HttpResponse
from django.contrib.auth.models import User, Group
from django.utils import simplejson

from ganeti_webmgr.authentication.models import ClusterUser


def search_users(request):
    """ search users and groups and return results as json """
    if 'term' in request.GET:
        term = request.GET['term']
    else:
        term = None

    if 'pk' in request.GET:
        pk = request.GET['pk']
    else:
        pk = None

    limit = 10
    if request.GET.get("groups", 'True') == 'True':
        data = simplejson.dumps(search_users_and_groups(term, pk, limit))
    else:
        data = simplejson.dumps(search_users_only(term, pk, limit))
    return HttpResponse(data, mimetype="application/json")


def search_owners(request):
    if 'term' in request.GET:
        term = request.GET['term']
    else:
        term = None

    if 'pk' in request.GET:
        pk = request.GET['pk']
    else:
        pk = None

    limit = 10
    data = simplejson.dumps(search_cluster_users(term, pk, limit))
    return HttpResponse(data, mimetype="application/json")


def search_cluster_users(term=None, pk=None, limit=10):

    if pk:
        clusterUsers = ClusterUser.objects.filter(id=int(pk))
    elif term:
        clusterUsers = ClusterUser.objects.filter(name__istartswith=term)
    else:
        clusterUsers = ClusterUser.objects.all()

    clusterUsers = clusterUsers.values('pk', 'name')

    if pk:
        query = clusterUsers[0]['name']
    elif term:
        query = term
    else:
        query = ""

    if limit:
        clusterUsers = clusterUsers[:limit]

    # lable each item based on its real_type
    labeledUsers = []
    for i in clusterUsers:
        f = 'other'
        userType = str(ClusterUser.objects.get(id=i['pk'])
                       .cast()._get_real_type())
        if userType == "profile":
            f = 'user'
        elif userType == "organization":
            f = 'group'
        labeledUsers.append((i['name'], f, i['pk']))

    clusterUsers = labeledUsers

    # sort list and crop out all but the top [limit] results
    clusterUsers = sorted(clusterUsers, key=lambda x: x[0])
    clusterUsers = clusterUsers if len(clusterUsers) \
        < limit else clusterUsers[:limit]

    return {
        'query': query,
        'results': clusterUsers
    }


def search_users_only(term=None, pk=None, limit=10):
    """
    Returns a list of the top N matches from Users with a name
    starting with term

    @param term: the term to search for
    @param limit: the number of results to return
    """
    if pk:
        users = User.objects.filter(id=int(pk))
    elif term:
        users = User.objects.filter(username__istartswith=term)
    else:
        users = User.objects.all()

    users = users.values('pk', 'username')

    if pk:
        query = users[0]['username']
    elif term:
        query = term
    else:
        query = ""

    if limit:
        users = users[:limit]

    # lable each item as a user
    f = 'user'
    users = [(i['username'], f, i['pk']) for i in users]

    # sort list and crop out all but the top [limit] results
    users = sorted(users, key=lambda x: x[0])
    users = users if len(users) \
        < limit else users[:limit]

    return {
        'query': query,
        'results': users
    }


def search_users_and_groups(term=None, pk=None, limit=10):
    """
    Returns a list of the top N matches from Groups and Users with a name
    starting with term.
    Warning: Searching for users and groups using a primary key will return
    a match from both users AND groups

    @param term: the term to search for
    @param pk: the primary key of the user/group to search for
    @param limit: the number of results to return
    """
    if pk:
        users = User.objects.filter(id=int(pk))
        groups = Group.objects.filter(id=int(pk))
    elif term:
        users = User.objects.filter(username__istartswith=term)
        groups = Group.objects.filter(name__istartswith=term)
    else:
        users = User.objects.all()
        groups = Group.objects.all()

    users = users.values('pk', 'username')
    groups = groups.values('pk', 'name')

    if pk:
        query = ""
    elif term:
        query = term
    else:
        query = ""

    if limit:
        users = users[:limit]
        groups = groups[:limit]

    # label each item as either user or a group
    f = 'user'
    users = [(i['username'], f, i['pk']) for i in users]
    f = 'group'
    groups = [(i['name'], f, i['pk']) for i in groups]

    # merge lists together
    # then sort lists and crop out all but the top [limit] results
    merged = users + groups
    merged = sorted(merged, key=lambda x: x[0])
    merged = merged if len(merged) < limit else merged[:limit]

    return {
        'query': query,
        'results': merged
    }
