from django.conf.urls.defaults import patterns, url

from .views import JobDetailView
from clusters.urls import cluster
job = '%s/job/(?P<job_id>\d+)' % cluster

urlpatterns = patterns(
    'jobs.views',

    url(r'^%s/status/?' % job, 'status', name='job-status'),

    url(r'^%s/clear/?' % job, 'clear', name='job-clear'),

    url(r'^%s/?' % job, JobDetailView.as_view(), name='job-detail'),
)
