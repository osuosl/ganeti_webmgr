try:
    from registration import register, grant, revoke, grant_group, \
        revoke_group, get_user_perms, get_model_perms

    __all__ = ('register', 'grant', 'revoke', 'grant_group', 'revoke_group', \
               'get_user_perms', 'get_model_perms')
except ImportError:
    pass