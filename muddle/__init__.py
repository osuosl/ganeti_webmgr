from django.conf import settings

from muddle.plugins.registerable import PERM_ALL, PERM_NONE, PERM_READ, \
                                    PERM_WRITE, PERM_CREATE, PERM_DELETE

VERSION = '0.1'
MUDDLE_ROOT = __file__[__file__.rfind('/')]

def settings_processor(request):
    """
    settings_processor adds settings required by most pages
    """
    return {
        'VERSION':VERSION,
        'MEDIA':'%s/muddle_static' % settings.SITE_ROOT,
        'ROOT':settings.SITE_ROOT
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
