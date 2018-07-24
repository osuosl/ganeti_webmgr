FROM osuosl/django-centos
MAINTAINER OSU Open Source Lab, support@osuosl.org

ENV DJANGO_SETTINGS_MODULE ganeti_webmgr.ganeti_web.settings
# allows developer to set up a volume mount by keeping config out of source dir
ENV GWM_CONFIG_DIR /opt/ganeti_webmgr_config

RUN yum install -y python-devel python-setuptools postgresql-devel gcc curl libffi-devel openssl-devel

WORKDIR /opt/ganeti_webmgr
VOLUME /opt/ganeti_webmgr
COPY ganeti_webmgr/ganeti_web/settings/config.yml.dist /opt/ganeti_webmgr_config/config.yml

# Keys generated specifically for Docker
# Do not use in a secure environment
RUN echo "DEBUG: true" >> /opt/ganeti_webmgr_config/config.yml && \
    echo "SECRET_KEY: \"f4iIZ1CTjeLvL3LEhf7m2TnhmIgmeOi1ZuooQ7OOdY\"" >> /opt/ganeti_webmgr_config/config.yml && \
    echo "WEB_MGR_API_KEY: \"Sfi7l83bjlGyYUBF4pIp/2vumfwPA+Lwz2ztu32LQ2k\"" >> /opt/ganeti_webmgr_config/config.yml
EXPOSE 8000
