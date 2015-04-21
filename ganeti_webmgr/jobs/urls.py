from django.conf.urls.defaults import patterns, url

from .views import JobDetailView
from ganeti_webmgr.clusters.urls import cluster
job = '%s/job/(?P<job_id>\d+)' % cluster

urlpatterns = patterns(
    'ganeti_webmgr.jobs.views',

    url(r'^%s/status/?' % job, 'status', name='job-status'),

    url(r'^%s/clear/?' % job, 'clear', name='job-clear'),

    url(r'^%s/?' % job, JobDetailView.as_view(), name='job-detail'),
)
