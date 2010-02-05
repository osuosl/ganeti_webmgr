import unittest

from managers import suite as managers_suite
from plugin import suite as plugins_suite

def suite():
    return unittest.TestSuite([
            managers_suite(),
            plugins_suite()
        ])

