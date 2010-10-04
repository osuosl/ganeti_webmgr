try:
    from registration import register, grant, revoke, grant_group, \
        revoke_group, get_user_perms, get_model_perms, revoke_all, get_users

    __all__ = ('register', 'grant', 'revoke', 'grant_group', 'revoke_group', \
               'get_user_perms', 'get_model_perms', 'revoke_all','get_users')
except ImportError:
    pass