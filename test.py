#!/usr/bin/python

import os
import sys
import unittest
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

sys.path.insert(0, './test')


#from test import suite as core_suite
 
#def suite():
#    return unittest.TestSuite([
#            core_suite()
#        ])

def test(*test_labels, **options):
    from django.conf import settings
    from django.test.utils import get_runner

    verbosity = int(options.get('verbosity', 1))
    interactive = options.get('interactive', True)
    test_runner = get_runner(settings)

    failures = test_runner(test_labels, verbosity=verbosity, interactive=interactive)
    if failures:
        sys.exit(failures)


if __name__ == '__main__':

    test('test_app')