class ListFile(object):
    """
    A file-like that wraps a list.  used primarily for writing lines to a list
    """
    def __init__(self, list):
        self.list = list
        self.write = list.append
