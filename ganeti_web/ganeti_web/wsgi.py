import os
from os.path import abspath, dirname
from sys import path

CURRENT_DIR = dirname(abspath(__file__))
APP_ROOT = dirname(CURRENT_DIR)
path.append(APP_ROOT)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "ganeti_web.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Apply WSGI middleware here.
# from helloworld.wsgi import HelloWorldApplication
# application = HelloWorldApplication(application)
