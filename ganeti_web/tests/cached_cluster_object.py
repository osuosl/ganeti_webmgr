# Copyright (C) 2010 Oregon State University et al.
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

import cPickle
from datetime import datetime
import time

from django.conf import settings
from django.test import TestCase

from ganeti_web.util import client
from ganeti_web.util.proxy import RapiProxy, CallProxy
from ganeti_web import models

Cluster = models.Cluster
CachedClusterObject = models.CachedClusterObject
TestModel = models.TestModel

__all__ = ('TestCachedClusterObject',)


class CachedClusterObjectBase(TestCase):
    """
    Base class for building testcases for CachedClusterObjects.  By extending
    this class and setting Model equal to the class to be tested this TestCase
    adds a series of tests to verify the caching mechanisms are working as
    intended for that model.
    """

    __LAZY_CACHE_REFRESH = None

    def setUp(self):
        self.__GanetiRapiClient = models.client.GanetiRapiClient
        models.client.GanetiRapiClient = RapiProxy
        self.__LAZY_CACHE_REFRESH = settings.LAZY_CACHE_REFRESH
        settings.LAZY_CACHE_REFRESH = 50

    def tearDown(self):
        TestModel.objects.all().delete()
        Cluster.objects.all().delete()

        models.client.GanetiRapiClient = self.__GanetiRapiClient

        if self.__LAZY_CACHE_REFRESH:
            settings.LAZY_CACHE_REFRESH = self.__LAZY_CACHE_REFRESH

    def create_model(self, **kwargs):
        """
        create an instance of the model being tested, this will instrument
        some methods of the model to check if they have been called
        """
        cluster, chaff = Cluster.objects.get_or_create(hostname='test.foo.org')
        obj = self.Model(cluster=cluster, **kwargs)
        
        # patch model class
        CallProxy.patch(obj, 'parse_transient_info')
        CallProxy.patch(obj, 'parse_persistent_info')
        CallProxy.patch(obj, '_refresh')
        CallProxy.patch(obj, 'load_info')
        CallProxy.patch(obj, 'save')
        return obj

    def test_trivial(self):
        """
        trivial test to instantiate class
        """
        self.create_model()

    def test_cached_object_init(self):
        """
        Trivial test to init model
        
        Verifies:
            * info is not loaded for new instance
            * info is loaded either by refresh or cached info for existing
              model
        """
        object = self.create_model()
        object.load_info.assertNotCalled(self)
        
        # XXX simulate loading existing instance by calling __init__ again and
        # passing a value for id
        object = self.create_model(id=1)
        object.__init__(1, cluster=object.cluster)
        object.load_info.assertCalled(self)
    
    def test_timestamp_precision(self):
        """
        Tests that timestamps can be stored with microsecond precision using
        PreciseDateTimeField.
        
        This may be database specific:
            * mysql - supported
            * sqlite - only 5 digits of precision
            * postgresql -
        """
        obj = self.create_model()
        timestamp = 1285883000.123456
        dt = datetime.fromtimestamp(timestamp)
        
        obj.mtime = dt
        obj.cached = dt
        obj.save()
        
        # XXX query values only. otherwise they may be updated
        values = TestModel.objects.filter(pk=obj.id).values('mtime','cached')[0]
        
        self.assertEqual(timestamp, float(values['mtime']))
        self.assertEqual(timestamp, float(values['cached']))
    
    def test_info(self):
        """
        Tests retrieving and setting info
        
        Verifies:
            * If serialized is available it will be deserialized and returned
            * If serialized info is not available, None will be returned
            * Setting info, clears serialized info. (delayed till save)
            * Setting info triggers info to be parsed
        """
        object = self.create_model()
        data = TestModel.data
        serialized_info = cPickle.dumps(data)
        
        # no serialized data, check twice for caching mechanism
        self.assertEqual(object.info, None)
        self.assertEqual(object.info, None)
        
        # set info
        object.info = data
        self.assertEqual(None, object.serialized_info)
        object.parse_transient_info.assertCalled(self)
        object.parse_persistent_info.assertCalled(self)
        
        # save causes serialization
        object.save()
        self.assertEqual(serialized_info, object.serialized_info)
        
        # serialized data, check twice for caching mechanism
        object.serialized_info = serialized_info
        self.assertEqual(object.info, data)
        self.assertEqual(object.info, data)

    def test_parse_info(self):
        """
        Test parsing info
        
        Verifies:
            * transient info is parsed
            * persistent info is parsed
        """
        obj = self.create_model(id=1)
        obj.parse_info()
        obj.parse_transient_info.assertCalled(self)
        obj.parse_persistent_info.assertCalled(self)
        
        self.assertEqual(obj.ctime, datetime.fromtimestamp(1285799513.4741000))
        self.assertEqual(obj.mtime, datetime.fromtimestamp(1285883187.8692000))
    
    def test_refresh(self, object=None):
        """
        Test forced refresh of cached data
        
        Verifies:
            * Object specific refresh is called
            * Info is parsed
            * Object is saved
            * Cache time is updated
        """
        object = object if object else self.create_model()
        object.save()
        now = datetime.now()
        object.refresh()
        
        object._refresh.assertCalled(self)
        object.parse_transient_info.assertCalled(self)
        object.parse_persistent_info.assertCalled(self)
        self.assertEqual(1, len(object.parse_persistent_info.calls))
        self.assertTrue(object.id)
        self.assertNotEqual(None, object.cached)
        self.assertTrue(now < object.cached, "Cache time should be newer")
    
    def test_refresh_error(self):
        """
        Test an error during refresh
        
        Verifies:
            * error will be saved in object.error
            * successful refresh after will clear error
        """
        object = self.create_model()
        msg = "SIMULATING AN ERROR"
        
        # force an error to test its capture
        object.throw_error = client.GanetiApiError(msg)
        object.save()
        object.refresh()
        self.assertEqual(msg, object.error)
        
        # clear the error and retry
        object.throw_error = None
        object.save()
        self.test_refresh(object)
        self.assertEqual(None, object.error)
    
    def test_lazy_cache(self):
        """
        Test that the lazy caching mechanism works
        
        Verifies:
            * If object.cached is None, refresh
            * If cache has timed out, refresh
            * otherwise parse cached transient info only
        """
        object = self.create_model()
        object.save()
        
        # no cache time
        object.load_info()
        object._refresh.assertCalled(self)
        object._refresh.reset()
        
        # cached, but not expired
        object.load_info()
        object._refresh.assertNotCalled(self)
        object.parse_transient_info.assertCalled(self)
        object.parse_transient_info.reset()
        
        # sleep to let cache expire
        time.sleep(.1)
        object.load_info()
        object._refresh.assertCalled(self)
        object._refresh.reset()
    
    def test_no_change_quick_update(self):
        """
        Tests that if no change has been made (signified by mtime), then an
        update query is used instead of Model.save()
        
        Verifies:
            * null Model.mtime causes save()
            * newer info.mtime causes save()
            * equal mtime causes update
        """
        object = self.create_model()
        object.save()
        object.save.reset()
        
        # mtime is None (object was never refreshed or parsed)
        object.refresh()
        object.save.assertCalled(self)
        object.save.reset()
        
        # mtime still the same as static data, no save
        object.refresh()
        object.save.assertNotCalled(self)
        
        # info.mtime newer, Model.save() called
        # XXX make a copy of the data to ensure this test does not conflict
        # with any other tests.
        data = object.data.copy()
        data['mtime'] = object.data['mtime'] + 100
        object.data = data
        object.refresh()
        object.save.assertCalled(self)
    
    def test_cache_disabled(self):
        """
        Tests that CachedClusterObjectBase.ignore_cache causes the cache to be
        ignored
        
        Verifies:
            * rapi call made even if mtime has not passed
            * object is still updated if mtime is new
        """
        object = self.create_model()
        object.save()
        
        # no cache time
        object.load_info()
        object._refresh.assertCalled(self)
        object._refresh.reset()
        
        # cache enabled
        object.load_info()
        object._refresh.assertNotCalled(self)
        
        # enable ignore cache, refresh should be called each time
        object.ignore_cache=True
        object.load_info()
        object._refresh.assertCalled(self)
        object._refresh.reset()
        object.load_info()
        object._refresh.assertCalled(self)
        object._refresh.reset()
        
        # cache re-enabled, cache should be used instead
        object.ignore_cache=False
        object.load_info()
        object._refresh.assertNotCalled(self)


class TestCachedClusterObject(CachedClusterObjectBase):
    Model = TestModel
