# This is imported as the DJANGO_SETTINGS_MODULE.
# First it trys to import end_user.py which should import base.py

# Returns a hopefully more useful error message if someone forgets to
# rename end_user.py.dist to end_user.py

try:
    from .end_user import *
except ImportError as e:
    msg = "(%s did you rename settings/end_user.py.dist?)"
    e.args = tuple([msg % e.args[0]])
    raise e