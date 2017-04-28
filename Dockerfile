FROM osuosl/python_webapp

RUN sed -i 's/WSGIPATH/ganeti_webmgr.ganeti_web/g' /etc/supervisor.d/app.conf
COPY . /opt/app/src
RUN yum install -y openssl-devel
RUN pip install .

ENV DJANGO_SETTINGS_MODULE ganeti_webmgr.ganeti_web.settings

# set up config file
COPY ./ganeti_webmgr/ganeti_web/settings/config.yml.dist /opt/ganeti_webmgr_config/config.yml

# Keys generated specifically for Docker
# Do not use in a secure environment
RUN echo "DEBUG: true" >> /opt/ganeti_webmgr_config/config.yml
RUN echo "SECRET_KEY: \"f4iIZ1CTjeLvL3LEhf7m2TnhmIgmeOi1ZuooQ7OOdY\"" >> /opt/ganeti_webmgr_config/config.yml
RUN echo "WEB_MGR_API_KEY: \"Sfi7l83bjlGyYUBF4pIp/2vumfwPA+Lwz2ztu32LQ2k\"" >> /opt/ganeti_webmgr_config/config.yml


RUN django-admin.py collectstatic --noinput --settings "ganeti_webmgr.ganeti_web.settings"
RUN django-admin.py syncdb --noinput --settings "ganeti_webmgr.ganeti_web.settings"

RUN echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'password')" | django-admin.py shell
