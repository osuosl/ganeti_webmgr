# define permission masks.  use 2.5 syntax for backwards compatibility
PERM_ALL    = int('1111',2)
PERM_NONE   = int('0000',2)
PERM_READ   = int('0001',2)
PERM_WRITE  = int('0010',2)
PERM_CREATE = int('0100',2)
PERM_DELETE = int('1000',2)

class Registerable(object):
    """
    Base class for objects that can be registered with
    """
    target = None
    _target = None
    permissions = PERM_NONE
