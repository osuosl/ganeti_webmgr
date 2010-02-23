class CyclicDependencyException(Exception):
    """
    Exception thrown when a cycle is detected within dependencies of a module
    """
    pass


class UnknownPluginException(Exception):
    """
    Exception thrown when attempting to access a plugin that has not been
    registered.
    """
    pass