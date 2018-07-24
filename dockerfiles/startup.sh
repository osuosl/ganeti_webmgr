#!/bin/bash
set -xe
trap /opt/ganeti_webmgr/dockerfiles/cleanup.sh EXIT
pip install .
rm -f ganeti.db
django-admin.py syncdb --noinput
django-admin.py syncdb --migrate --noinput
echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'password')" | django-admin.py shell
django-admin.py runserver 0.0.0.0:8000
