

"""
Loading this module changes the state in another module.  We can check the state
in the other module to know whether or not this module was actually loaded
"""
from ganeti_webmgr.muddle.tests.apps.load_app_plugin import verify
verify.MODULE_LOADED = True

