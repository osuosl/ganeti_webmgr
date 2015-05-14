FROM centos:7

MAINTAINER OSU Open Source Lab, support@osuosl.org


EXPOSE 8000
ENV DJANGO_SETTINGS_MODULE ganeti_webmgr.ganeti_web.settings
# allows developer to set up a volume mount by keeping config out of source dir
ENV GWM_CONFIG_DIR /opt/ganeti_webmgr_config

RUN yum install -y python-devel python-setuptools postgresql-devel gcc curl libffi-devel openssl-devel

RUN easy_install pip


WORKDIR /opt/ganeti_webmgr
COPY . /opt/ganeti_webmgr
COPY ./ganeti_webmgr/ganeti_web/settings/config.yml.dist /opt/ganeti_webmgr_config/config.yml

# Keys generated specifically for Docker
# Do not use in a secure environment
RUN echo "DEBUG: true" >> /opt/ganeti_webmgr_config/config.yml
RUN echo "SECRET_KEY: \"f4iIZ1CTjeLvL3LEhf7m2TnhmIgmeOi1ZuooQ7OOdY\"" >> /opt/ganeti_webmgr_config/config.yml
RUN echo "WEB_MGR_API_KEY: \"Sfi7l83bjlGyYUBF4pIp/2vumfwPA+Lwz2ztu32LQ2k\"" >> /opt/ganeti_webmgr_config/config.yml

RUN pip install .
RUN django-admin.py syncdb --noinput
RUN django-admin.py syncdb --migrate --noinput
RUN echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'password')" | django-admin.py shell
CMD ["django-admin.py", "runserver", "0.0.0.0:8000"]