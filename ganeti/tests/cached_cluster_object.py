import cPickle
from datetime import datetime
import time

from django.conf import settings
from django.test import TestCase

from util import client
from ganeti.tests.rapi_proxy import RapiProxy
from ganeti import models
CachedClusterObject = models.CachedClusterObject


__all__ = ('TestCachedClusterObject',)


class TestModel(CachedClusterObject):
    """ simple implementation of a cached model that has been instrumented """
    
    data = {'a':1, 'b':'c', 'd':[1,2,3]}
    parsed_persistent = False
    parsed_transient = False
    refreshed = False
    throw_error = None
    
    def parse_persistent_info(self):
        self.parsed_persistent = True
    
    def parse_transient_info(self):
        self.parsed_transient = True
    
    def _refresh(self):
        if self.throw_error:
            raise self.throw_error
        self.refreshed = True
        return {}

    def save(self, *args, **kwargs):
        self.id = 1


class CachedClusterObjectBase(TestCase):
    """
    Base class for building testcases for CachedClusterObjects.
    """
    
    __GanetiRapiClient = None
    
    def setUp(self):
        self.tearDown()
        self.__GanetiRapiClient = models.client.GanetiRapiClient
        models.client.GanetiRapiClient = RapiProxy
    
    def tearDown(self):
        if self.__GanetiRapiClient is not None:
            models.client.GanetiRapiClient = self.__GanetiRapiClient

    def test_trivial(self):
        """
        trivial test to instantiate class
        """
        self.Model()

    def test_cached_object_init(self):
        """
        Trivial test to init model
        
        Verifies:
            * info is not loaded for new instance
            * info is loaded either by refresh or cached info for existing
              model
        """
        object = self.Model()
        self.assertFalse(object.refreshed or object.parsed_transient)
        
        # simulate loading existing instance by passing in id
        object = TestModel(id=1)
        self.assert_(object.refreshed or object.parsed_transient)
    
    def test_info(self):
        """
        Tests retrieving and setting info
        
        Verifies:
            * If serialized is available it will be deserialized and returned
            * If serialiezed info is not available it will be returned
            * Setting info serializes info automatically
            * Setting info triggers info to be parsed
        """
        object = self.Model()
        data = TestModel.data
        serialized_info = cPickle.dumps(data)
        
        # no serialized data, check twice for caching mechanism
        self.assertEqual(object.info, None)
        self.assertEqual(object.info, None)
        
        # set info
        object.info = data
        self.assertEqual(object.serialized_info, serialized_info)
        self.assert_(object.parsed_transient)
        self.assert_(object.parsed_persistent)
        
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
        object = self.Model()
        object.parse_info()
        self.assert_(object.parsed_transient)
        self.assert_(object.parsed_persistent)
    
    def test_refresh(self, object=None):
        """
        Test forced refresh of cached data
        
        Verifies:
            * Object specific refresh is called
            * Info is parsed
            * Object is saved
            * Cache time is updated
        """
        object = object if object else self.Model()
        now = datetime.now()
        object.refresh()
        
        self.assert_(object.refreshed)
        self.assert_(object.parsed_transient)
        self.assert_(object.parsed_persistent)
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
        object = self.Model()
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
        object = self.Model()
        object.save()
        
        # no cache time
        object.load_info()
        self.assert_(object.refreshed)
        
        # cached, but not expired
        object.refreshed = False
        object.load_info()
        self.assertFalse(object.refreshed)
        self.assert_(object.parsed_transient)
        
        # sleep to let cache expire
        time.sleep(.1)
        object.load_info()
        self.assert_(object.refreshed)

class TestCachedClusterObject(CachedClusterObjectBase):
    Model = TestModel