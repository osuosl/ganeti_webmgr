#!/usr/bin/env python
# coding: utf-8

from setuptools import setup, find_packages
from ganeti_webmgr import __version__ as version

readme = open('README.rst').read()
changelog = open('CHANGELOG.rst').read().replace('.. :changelog:', '')
requirements = open('requirements/production.txt').read().splitlines()

setup(
    name='ganeti_webmgr',
    version=version,

    # metadata
    description=('Ganeti Web Manager is a Django based web frontend for'
                 ' managing Ganeti virtualization clusters.'),
    long_description=readme + '\n\n' + changelog,
    keywords='ganeti web manager django',
    author='Oregon State University Open Source Lab',
    author_email='info@osuosl.org',
    url='https://github.com/osuosl/ganeti_webmgr',

    # package
    packages=find_packages(exclude=["docs"]),  # should find package easily
    install_requires=requirements,

    # easiest way to install templates, static files, translation files etc.
    include_package_data=True,

    entry_points = {
        'console_scripts': [
            # FIXME (Path problems it seems)
            # 'gwm-manage = ganeti_webmgr.manage:main',
        ],
    },

    # in case you want to have easy testing in future by `./setup.py test`
    # you'd need to work with setuptools documentation:
    #  http://pythonhosted.org/setuptools/setuptools.html
    #test_suite='tests',

    # other meta and legal information
    license="GPLv2",
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
)
