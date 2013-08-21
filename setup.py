#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from setuptools import setup

from ganeti_webmgr import __VERSION__

if sys.argv[-1] == 'publish':
    os.system('python setup.py sdist upload')
    sys.exit()

readme = open('README.rst').read()
changelog = open('CHANGELOG.rst').read().replace('.. :changelog:', '')

setup(
    name='ganeti_webmgr',
    version=".".join(__VERSION__),
    description=('Ganeti Web Manager is a Django based web frontend for'
                 + ' managing Ganeti virtualization clusters.'),
    long_description=readme + '\n\n' + changelog,
    author='Oregon State University Open Source Lab',
    author_email='info@osuosl.org',
    url='https://github.com/osuosl/ganeti_webmgr',
    packages=[
        'ganeti_webmgr',
    ],
    package_dir={'ganeti_webmgr': 'ganeti_webmgr'},
    include_package_data=True,
    install_requires=[
    ],
    license="GPLv2",
    zip_safe=False,
    keywords='ganeti web manager django',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: Django',
        'Intended Audience :: System Administrators',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Natural Language :: English',
        'Natural Language :: Greek',
        'Natural Language :: Spanish',
        "Programming Language :: Python :: 2",
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Operating System :: POSIX',
        'Operating System :: POSIX :: Linux',
        'Topic :: System :: Clustering',
        'Topic :: System :: Networking',
        'Topic :: System :: Systems Administration',
    ],
    #test_suite='tests',  # XXX: need to fix that
)
