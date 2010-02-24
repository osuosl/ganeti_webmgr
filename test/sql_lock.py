import unittest
import time

from muddle.models import SQLLock

def suite():
    return unittest.TestSuite([
            unittest.TestLoader().loadTestsFromTestCase(SQLLock_Test)
        ])


class SQLLock_Test(unittest.TestCase):
   
    def test_lock_reaquire(self):
        """
        Tests a single lock reacquiring.  The id should stay the same unless
        the lock has expired.  reacquiring extends the timeout.
        """
        a = SQLLock()
        self.assert_(a.acquire('test',10000))
        id = a.id
        self.assert_(a.acquire('test',10000))
        self.assertEquals(id, a.id)
    
    def test_reacquire_timedout(self):
        """
        Tests a single lock reacquiring after the lock has already timed out.
        The id should be different if it reacquires after timeout
        """
        a = SQLLock()
        self.assert_(a.acquire('test2',500))
        id = a.id
        time.sleep(1)
        self.assert_(a.acquire('test2',1000))
        self.assertNotEquals(id, a.id)
    
    def test_lock_contention(self):
        """
        Tests two locks contending for the same lock.
        """
        a = SQLLock()
        b = SQLLock()
        self.assert_(a.acquire('test3',1000))
        self.assertFalse(b.acquire('test3',5000))
        time.sleep(2)
        self.assertTrue(b.acquire('test3',1000))