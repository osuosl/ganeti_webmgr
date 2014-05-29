from yaml import load
from .helpers import DEFAULT_CONFIG_PATH

# Open our yaml config and override settings values with it's config
try:
    config_file = open(DEFAULT_CONFIG_PATH)
    for key, value in load(config_file.read()).items():
        globals()[key] = value
    config_file.close()
except:
    print "Could not find, or open config located at %s" % DEFAULT_CONFIG_PATH
