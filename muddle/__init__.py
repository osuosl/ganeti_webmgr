from django.conf import settings as django_settings

VERSION = '0.1'
MUDDLE_ROOT = __file__[__file__.rfind('/')]

def settings_processor(request):
    """
    settings_processor adds settings required by most pages
    """
    return {
        'VERSION':VERSION,
        'STATIC':'%s/muddle_static' % django_settings.SITE_ROOT,
        'ROOT':django_settings.SITE_ROOT
    }
