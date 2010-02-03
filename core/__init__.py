import settings


def settings_processor(request):
    """
    settings_processor adds settings required by most pages
    """
    return {
        'VERSION':settings.VERSION,
        'MEDIA':settings.MEDIA_URL,
        'ROOT':settings.ROOT_URL
    }