import unittest

from modules import suite as modules_suite

def suite():
    return unittest.TestSuite([
            modules_suite()
        ])

