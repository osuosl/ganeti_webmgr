from distutils.core import setup

setup(
    name='ganeti-webmgr',
    version='0.9.2',
    author='Peter Krenesky',
    author_email='peter@osuosl.org',
    maintainer='Ken Lett',
    maintainer_email='ken@osuosl.org',
    license='GPLv2',
    url='http://code.osuosl.org/projects/ganeti-webmgr',
    long_description=open('README').read(),
    packages=['ganeti-webmgr',],
    install_requires=open('ganeti-webmgr/requirements.txt').read().split('\n'),
)
