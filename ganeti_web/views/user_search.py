from django.http import HttpResponse
from django.contrib.auth.models import User, Group
from django.utils import simplejson
from ganeti_web.models import ClusterUser

def search_users(request):
    """ search users and groups and return results as json """
    if 'term' not in request.GET:
        return HttpResponse()

    term = request.GET['term']
    limit = 10
    if request.GET.get("groups", 'True') == 'True':
        data = simplejson.dumps(search_users_and_groups(term, limit))
    else:
        data = simplejson.dumps(search_users_only(term, limit))
    return HttpResponse(data, mimetype="application/json")

def search_owners(request):
    term = request.GET['term']
    limit = 10
    data = simplejson.dumps(search_cluster_users(term, limit))
    return HttpResponse(data, mimetype="application/json")

def search_cluster_users(term=None, limit=10):
    if term:
        clusterUsers = ClusterUser.objects.filter(name__istartswith=term)
    else:
        clusterUsers = ClusterUser.objects.all()
    
    clusterUsers = clusterUsers.values('pk', 'name')
     
    if limit: 
        clusterUsers = clusterUsers[:limit]
     
    # lable each item based on its real_type
    labeledUsers = []
    for i in clusterUsers:
        f = 'other'
        userType = str(ClusterUser.objects.get(id=i['pk']).cast()._get_real_type())
        if userType == "profile":  
            f = 'user'             
        elif userType == "organization":   
            f = 'group' 
        labeledUsers.append((i['name'], f, i['pk']))
    
    clusterUsers = labeledUsers 
   
    # sort list and crop out all but the top [limit] results
    clusterUsers = sorted(clusterUsers, key=lambda x: x[0]) 
    clusterUsers = clusterUsers if len(clusterUsers) < limit else clusterUsers[:limit]
 
    return {
        'query':term,
        'results':clusterUsers
    }


def search_users_only(term=None, limit=10):
    """
    Returns a list of the top N matches from Users with a name
    starting with term
 
    @param term: the term to search for
    @param limit: the number of results to return
    """
     
    if term:
        users = User.objects.filter(username__istartswith=term)
    else:
        users = User.objects.all()
     
    users = users.values('pk', 'username')
     
    if limit: 
        users = users[:limit]
     
    # lable each item as a user
    f = 'user'
    users = [(i['username'], f, i['pk']) for i in users]
     
    # sort list and crop out all but the top [limit] results
    users = sorted(users, key=lambda x: x[0]) 
    users = users if len(users) < limit else users[:limit]
 
    return {
        'query':term,
        'results':users
    }

def search_users_and_groups(term=None, limit=10):
    """
    Returns a list of the top N matches from Groups and Users with a name
    starting with term

    @param term: the term to search for
    @param limit: the number of results to return
    """
    
    if term:
        users = User.objects.filter(username__istartswith=term)
        groups = Group.objects.filter(name__istartswith=term)
    else:
        users = User.objects.all()
        groups = Group.objects.all()

    users = users.values('pk', 'username')
    groups = groups.values('pk', 'name')

    if limit:
        users = users[:limit]
        groups = groups [:limit]

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
        'query':term,
        'results':merged
    }
