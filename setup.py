#!/usr/bin/env python
from distutils.core import setup
import os

def fullsplit(path, result=None):
    """
    Split a pathname into components (the opposite of os.path.join) in a
    platform-neutral way.
    
    shamelessly borrowed from django
    """
    if result is None:
        result = []
    head, tail = os.path.split(path)
    if head == '':
        return [tail] + result
    if head == path:
        return result
    return fullsplit(head, [tail] + result)


# Compile the list of packages available, because distutils doesn't have
# an easy way to do this.
#
# shamelessly borrowed from django
packages, package_data = [], []
root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)
muddle_dir = 'muddle'

for dirpath, dirnames, filenames in os.walk(muddle_dir):
    # Ignore dirnames that start with '.'
    for i, dirname in enumerate(dirnames):
        if dirname.startswith('.'): del dirnames[i]
    if '__init__.py' in filenames:
        packages.append('.'.join(fullsplit(dirpath)))
    elif filenames:
        for f in filenames:
            package_data.append(os.path.join(dirpath, f)[7:])

setup(name='Muddle',
      version='0.0.1',
      description='Muddle ',
      long_description = 'Muddle is a Django App that provides plugin management and automatic view and editing page generation.',
      maintainer='Peter Krenesky',
      maintainer_email='peter@osuosl.org',
      url='http://trac.osuosl.org/muddle',
      packages=packages,
      package_data={'muddle':package_data},
      requires = ['django'],
      provides = ['muddle'],
      license='Apache 2.0'
     )