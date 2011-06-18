from tastypie.authorization import Authorization

__author__ = 'bojan'

class SuperuserAuthorization(Authorization):
    def is_authorized(self, request, object=None):
        user = request.user
        if not user.is_superuser:
            return False
        return True
    def get_identifier(self, request):
        return request.user.username
