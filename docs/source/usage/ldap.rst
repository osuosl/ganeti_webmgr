LDAP
====

This is a tentative guide to using LDAP authentication in GWM.

First, add ``django_auth_ldap.backend.LDAPBackend`` to
``AUTHENTICATION_BACKENDS`` in your ``settings.py`` file.

Then, add something like the following snippet, and adjust to taste:

::

    # LDAP Authentication via django-auth-ldap
    # If you need to debug your configuration, see:
    #       http://packages.python.org/django-auth-ldap/#logging
    # Set AUTH_LDAP_SERVER_URI to the server you will authenticate against.
    # If you want to bind as a specific user, update AUTH_LDAP_BIND_DN and
    #       AUTH_LDAP_BIND_PASSWORD appropriately.  Leave blank to bind
    #       anonymously.
    # Specify where to search in LDAP via AUTH_LDAP_USER_SEARCH.
    # You can also define user attributes based on those found in LDAP.
    #       Update AUTH_LDAP_USER_ATTR_MAP as needed.
    import ldap
    from django_auth_ldap.config import LDAPSearch, GroupOfNamesType
    AUTH_LDAP_SERVER_URI = "ldaps://ldap.example.com" 
    AUTH_LDAP_BIND_DN = "" 
    AUTH_LDAP_BIND_PASSWORD = "" 
    AUTH_LDAP_USER_SEARCH = LDAPSearch("ou=People,dc=example,dc=com",
            ldap.SCOPE_SUBTREE, "(uid=%(user)s)")
    AUTH_LDAP_USER_ATTR_MAP = {
        "fist_name": "givenName",
        "last_name": "sn",
        "email": "mail" 
    }

    # If you want to perform group-based authorization, update the
    # following as needed.
    # You can set user flags based on group membership via
    #       AUTH_LDAP_USER_FLAGS_BY_GROUP.
    # You can also require the user be a member of a group so as to be
    # authorized to log in.  Likewise, you can ban users based on group
    # membership.
    AUTH_LDAP_GROUP_SEARCH = LDAPSearch("ou=Group,dc=example,dc=com",
            ldap.SCOPE_SUBTREE, "(objectClass=groupOfNames")
    AUTH_LDAP_GROUP_TYPE = GroupOfNamesType(name_attr="cn")
    AUTH_LDAP_USER_FLAGS_BY_GROUP = {
        "is_active": "cn=Operators,ou=Group,dc=example,dc=com",
        "is_staff": "cn=Staff,ou=Group,dc=example,dc=com",
        "is_superuser": "cn=Privileged,ou=Group,dc=example,dc=com",
    }
    AUTH_LDAP_REQUIRE_GROUP = "cn=Operators,ou=Group,dc=example,dc=com" 
    AUTH_LDAP_DENY_GROUP = "cn=Banned,ou=Group,dc=example,dc=com" 
