# Copyright (C) 2010 Oregon State University et al.
# Copyright (C) 2010 Greek Research and Technology Network
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301,
# USA.

from django.conf import settings

from django.contrib.sites import models as sites_app
from django.contrib.sites.management import create_default_site
from django.contrib.sites.models import Site

from django.db.models.signals import post_syncdb

def update_sites_module(sender, **kwargs):
    """
    Create a new row in the django_sites table that
      holds SITE_ID, SITE_NAME and SITE_DOMAIN defined
      in setting.py
      
      If SITE_NAME or SITE_DOMAIN are not defined they
       will default to 'example.com'
    """
    id, name, domain = (1, 'example.com', 'example.com')
    try:
        id = settings.SITE_ID
    except AttributeError, e:
        print e
        print 'Using: \'%s\' for site id.' % id

    try:
        name = settings.SITE_NAME
    except AttributeError, e:
        print e
        print 'Using: \'%s\' for site name.' % name

    try:
        domain = settings.SITE_DOMAIN
    except AttributeError, e:
        print e
        print 'Using: \'%s\' for site domain.' % domain
    
    try:
        site = Site.objects.get(id=id)
    except Site.DoesNotExist:
        if kwargs['verbosity'] >= 1:
            print "New site: [%s] %s (%s) created in django_site table." % \
                (id, name, domain)
        site = Site(id=id, name=name, domain=domain)
        site.save()
        # Reconnect create_default_site request for other apps
        post_syncdb.connect(create_default_site, sender=sites_app)
    else:
        if site.name != name:
            print "A site with the id of %s is already taken. " \
            "Please change SITE_ID to a different number in your " \
            "settings.py file." % id
