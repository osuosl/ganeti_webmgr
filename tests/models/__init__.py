import unittest

from form import suite as form_suite

def suite():
    return unittest.TestSuite([
            form_suite()
        ])
