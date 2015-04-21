def path_to_class(path):
    """  convert path string into class """
    last_dot = path.rfind('.')
    from_ = path[:last_dot]
    name = path[last_dot+1:]
    module = __import__(from_, {}, {}, [name])
    try:
        return module.__dict__[name]
    except KeyError:
        # XXX raise as import error
        raise ImportError()
