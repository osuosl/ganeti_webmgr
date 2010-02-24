import unittest

from test import suite as core_suite
 
def suite():
    return unittest.TestSuite([
            core_suite()
        ])