from django.conf import settings

from muddle.plugins.registerable import PERM_ALL, PERM_NONE, PERM_READ, \
                                    PERM_WRITE, PERM_CREATE, PERM_DELETE

def settings_processor(request):
    """
    settings_processor adds settings required by most pages
    """
    return {
        'VERSION':settings.VERSION,
        'MEDIA':settings.MEDIA_URL,
        'ROOT':settings.ROOT_URL
    }


def perms_processor(request):
    """
    settings_processor adds default permission masks
    """
    return {
        'PERM_ALL':PERM_ALL,
        'PERM_NONE':PERM_NONE,
        'PERM_READ':PERM_READ,
        'PERM_WRITE':PERM_WRITE,
        'PERM_CREATE':PERM_CREATE,
        'PERM_DELETE':PERM_DELETE
    }