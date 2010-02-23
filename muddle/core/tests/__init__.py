import unittest

from plugins import suite as plugins_suite
from sql_lock import suite as sqllock_suite
from permissions import suite as permissions_suite
from model_support import suite as model_support_suite
from models import suite as model_suite

def suite():
    return unittest.TestSuite([
            plugins_suite(),
            #sqllock_suite(),
            permissions_suite(),
            model_support_suite(),
            model_suite()
        ])

