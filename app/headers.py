import typing

from collections import defaultdict

class Headers:
    """
    Save HTTP request header(s) as a dictionary that k-v partition by ':'
    """
    def __init__(self):
        self._headers = defaultdict(list)
    
    def add(self, name, value):
        self._headers[name.lower()].append(value)
    
    def get_all(self, name):
        return self._headers[name.lower()]

    def get(self, name, default=None):
        try:
            return self.get_all(name)[-1]
        except IndexError:
            return default
