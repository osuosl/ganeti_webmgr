def dict_key(dict, value):
    """finds key for the value in this dict"""
    for k,v in dict.items():
        if value==v:
            return k
