import inspect

from django.conf import settings

from ganeti_webmgr.muddle.util import path_to_class


def load_app_plugin(module_name, Klass=None, method=None):
    """
    Helper method for loading an app plugin.  An app plugin is defined as some
    form of plugin that uses a form of registration logic that other apps must
    use to register their usage of the plugin.

    Some examples built into django:
        * models found within models.py
        * admin classes within admin.py

    @param module_name: module name to load.  This is a string,
    @param klass: class type(s) to load.  This may be a single class or a list
    of classes.
    @param method: method to run passing in each class that is found, or the
    module if no classes are specified
    """

    for app in settings.INSTALLED_APPS:
        try:
            module = path_to_class('.'.join([app, module_name]))

            if Klass is not None:
                assert(callable(method))

                for name in dir(module):
                    # run the method for each member
                    obj = getattr(module, name)
                    if inspect.isclass(obj) and issubclass(obj, (Klass,)):
                        method(obj)

            elif callable(method):
                # no classes specified, but there was a method. execute the method
                # with the module
                method(module)

            else:
                # no class or method, importing the module is enough
                pass
        except ImportError:
            # not all apps will have the module we are looking for
            pass