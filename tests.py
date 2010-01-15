import unittest

from core.tests import suite as core_suite

def suite():
    return unittest.TestSuite([
            core_suite()
        ])
