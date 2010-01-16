import unittest

from plugins import suite as plugins_suite

def suite():
    return unittest.TestSuite([
            plugins_suite()
        ])

