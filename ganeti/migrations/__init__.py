
def db_table_exists(table, cursor=None):
    """
    Determine if a table exists in the database

    cribbed from:
    https://gist.github.com/527113/307c2dec09ceeb647b8fa1d6d49591f3352cb034
    """

    try:
        if not cursor:
            from django.db import connection
            cursor = connection.cursor()
        if not cursor:
            raise Exception
        table_names = connection.introspection.get_table_list(cursor)
    except:
        raise Exception("unable to determine if the table '%s' exists" % table)
    else:
        return table in table_names