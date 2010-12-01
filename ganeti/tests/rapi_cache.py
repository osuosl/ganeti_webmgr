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


from django.test import TestCase

from ganeti.models import get_rapi, clear_rapi_cache, RAPI_CACHE, \
    RAPI_CACHE_HASHES, Cluster
from util import client

__all__ = ('TestRapiCache',)


class TestRapiCache(TestCase):
    
    def setUp(self):
        self.cluster = Cluster(hostname='ganeti.osuosl.test')
        self.cluster.save()
    
    def tearDown(self):
        clear_rapi_cache()
        Cluster.objects.all().delete()
    
    def test_get_with_cluster(self):
        """
        Test getting a new rapi for a cluster
        
        Verifies:
            * rapi is returned
        """
        cluster = self.cluster
        rapi = get_rapi(cluster.hash, cluster)
        self.assert_(rapi)
        self.assert_(isinstance(rapi, (client.GanetiRapiClient,)))
    
    def test_get_with_id(self):
        """
        Test getting a new rapi for a cluster by cluster ID
        Verifies:
            * rapi is returned
        """
        cluster = self.cluster
        rapi = get_rapi(cluster.hash, cluster.id)
        self.assert_(rapi)
        self.assert_(isinstance(rapi, (client.GanetiRapiClient,)))
    
    def test_get_cached_client(self):
        """
        Test getting a cached rapi
        
        Verifies:
            * rapi returned is the same as the cached rapi
        """
        cluster = self.cluster
        rapi = get_rapi(cluster.hash, cluster.id)
        self.assert_(rapi)
        self.assert_(isinstance(rapi, (client.GanetiRapiClient,)))
        
        cached_rapi = get_rapi(cluster.hash, cluster)
        self.assertEqual(rapi, cached_rapi)
        
        cached_rapi = get_rapi(cluster.hash, cluster.id)
        self.assertEqual(rapi, cached_rapi)
    
    def test_get_changed_hash(self):
        """
        Test getting rapi after hash has changed
        
        Verifies:
            * a new rapi is created and returned
            * old rapi is removed from cache
            * reverse cache is now pointing to new hash
        """
        cluster = self.cluster
        old_hash = cluster.hash
        rapi = get_rapi(cluster.hash, cluster)
        
        cluster.hostname = 'a.different.hostname'
        cluster.save()
        self.assertNotEqual(old_hash, cluster.hash, "new hash was not created")
        new_rapi = get_rapi(cluster.hash, cluster)
        self.assert_(rapi)
        self.assert_(isinstance(rapi, (client.GanetiRapiClient,)))
        self.assertNotEqual(rapi, new_rapi)
        self.assertFalse(old_hash in RAPI_CACHE, "old rapi client was not removed")
    
    def test_stale_hash(self):
        """
        Tests an object with a stale hash
        
        Verifies:
            * a rapi is created and stored using the current credentials
        """
        cluster = self.cluster
        stale_cluster = Cluster.objects.get(id=cluster.id)
        cluster.hostname = 'a.different.hostname'
        cluster.save()
        clear_rapi_cache()
        stale_rapi = get_rapi(stale_cluster.hash, stale_cluster)
        self.assert_(stale_rapi)
        self.assert_(isinstance(stale_rapi, (client.GanetiRapiClient,)))
        
        fresh_rapi = get_rapi(cluster.hash, cluster)
        self.assertEqual(stale_rapi, fresh_rapi)
    
    def test_stale_hash_new_already_created(self):
        """
        Tests an object with a stale hash, but the new client was already
        created
        
        Verifies:
            * Existing client, with current hash, is returned
        """
        cluster = self.cluster
        stale_cluster = Cluster.objects.get(id=cluster.id)
        cluster.hostname = 'a.different.hostname'
        cluster.save()
        clear_rapi_cache()
        fresh_rapi = get_rapi(cluster.hash, cluster)
        stale_rapi = get_rapi(stale_cluster.hash, stale_cluster)
        self.assert_(stale_rapi)
        self.assert_(isinstance(stale_rapi, (client.GanetiRapiClient,)))
        self.assertEqual(stale_rapi, fresh_rapi)