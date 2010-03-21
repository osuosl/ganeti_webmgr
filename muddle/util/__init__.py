def dict_key(dict, value):
    """finds key for the value in this dict"""
    for k,v in dict.items():
        if value==v:
            return k


def path_to_class(path):
    """  convert path string into class """
    last_dot = path.rfind('.')
    from_ = path[:last_dot]
    name = path[last_dot+1:]
    return __import__(from_, {}, {}, [name]).__dict__[name]