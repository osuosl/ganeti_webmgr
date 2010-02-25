import unittest

from form import suite as form_suite
from wrapper import suite as wrapper_suite


def suite():
    return unittest.TestSuite([
            form_suite(),
            wrapper_suite(),
        ])
