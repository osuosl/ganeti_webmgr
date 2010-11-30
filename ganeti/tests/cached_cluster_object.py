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

from util import client
from ganeti.tests.rapi_proxy import RapiProxy
from ganeti.tests.call_proxy import CallProxy
from ganeti import models
CachedClusterObject = models.CachedClusterObject


__all__ = ('TestCachedClusterObject',)


class TestModel(CachedClusterObject):
    """ simple implementation of a cached model that has been instrumented """
    
    data = {'mtime': 1285883187.8692031, 'ctime': 1285799513.4741089}
    throw_error = None
    
    def _refresh(self):
        if self.throw_error:
            raise self.throw_error
        return self.data

    def save(self, *args, **kwargs):
        self.id = 1


class CachedClusterObjectBase(TestCase):
    """
    Base class for building testcases for CachedClusterObjects.  By extending
    this class and setting Model equal to the class to be tested this TestCase
    adds a series of tests to verify the caching mechanisms are working as
    intended for that model.
    """
    
    __GanetiRapiClient = None
    
    def setUp(self):
        self.tearDown()
        self.__GanetiRapiClient = models.client.GanetiRapiClient
        models.client.GanetiRapiClient = RapiProxy
        
    def create_model(self, *args):
        """
        create an instance of the model being tested, this will instrument
        some methods of the model to check if they have been called
        """
        object = self.Model(*args)
        
        # patch model class
        CallProxy.patch(object, 'parse_transient_info')
        CallProxy.patch(object, 'parse_persistent_info')
        CallProxy.patch(object, '_refresh')
        CallProxy.patch(object, 'load_info')
        return object
    
    def tearDown(self):
        if self.__GanetiRapiClient is not None:
            models.client.GanetiRapiClient = self.__GanetiRapiClient

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
        object = self.create_model(1)
        object.__init__(1)
        object.load_info.assertCalled(self)
    
    def test_info(self):
        """
        Tests retrieving and setting info
        
        Verifies:
            * If serialized is available it will be deserialized and returned
            * If serialiezed info is not available it will be returned
            * Setting info serializes info automatically
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
        self.assertEqual(object.serialized_info, serialized_info)
        object.parse_transient_info.assertCalled(self)
        object.parse_persistent_info.assertCalled(self)
        
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
        object = self.create_model(1)
        object.parse_info()
        object.parse_transient_info.assertCalled(self)
        object.parse_persistent_info.assertCalled(self)
        
        self.assertEqual(object.ctime, datetime.fromtimestamp(1285799513.4741089))
        self.assertEqual(object.mtime, datetime.fromtimestamp(1285883187.8692031))
    
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
        now = datetime.now()
        object.refresh()
        
        object._refresh.assertCalled(self)
        object.parse_transient_info.assertCalled(self)
        object.parse_persistent_info.assertCalled(self)
        self.assertEqual(1, len(object.parse_persistent_info.calls))
        self.assert_(object.id)
        self.assertNotEqual(None, object.cached)
        self.assert_(now < object.cached, "Cache time should be newer")
    
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
        object.refresh()
        self.assertEqual(msg, object.error)
        
        # clear the error and retry
        object.throw_error = None
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
        settings.LAZY_CACHE_REFRESH = 50
        object = self.create_model()
        object.save()
        
        # no cache time
        object.load_info()
        object._refresh.assertCalled(self)
        
        # cached, but not expired
        object.refreshed = False
        object.load_info()
        self.assertFalse(object.refreshed)
        object.parse_transient_info.assertCalled(self)
        
        # sleep to let cache expire
        time.sleep(.1)
        object.load_info()
        object._refresh.assertCalled(self)

class TestCachedClusterObject(CachedClusterObjectBase):
    Model = TestModel