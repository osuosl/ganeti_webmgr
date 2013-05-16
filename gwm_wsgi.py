# activate virtual environment
activate_this = '%s/bin/activate_this.py' % "."
execfile(activate_this, dict(__file__=activate_this))

#import newrelic.agent
#newrelic.agent.initialize("/home/chance/ganeti_webmgr/newrelic.ini")

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "settings")

# This application object is used by the development server
# as well as any WSGI server configured to use this file.

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
application = newrelic.agent.wsgi_application()(application)
