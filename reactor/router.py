import re
import functools
from collections import OrderedDict, defaultdict

class Router:
    def __init__(self):
        self.routes_by_method = defaultdict(OrderedDict)
        self.names = set()
        
    def add_router(self, name, method, path, handler):
        """keep a pair ((name, mothod, path): handler)

        Args:
            name (str): used to identify the function is not repeated
            method (str): HTTP method
            path (str): url path
            handler (function obj): bussinese logic function object,

        Raises:
            ValueError: current router already exists.
        """
        assert path.startswith("/"), "paths must start with '/'"
        if name in self.names:
            raise ValueError(f"A router named {name} already exists.")
        
        route_template = ""
        for segment in path.split("/")[1:]:
            if segment.startswith("{") and segment.endswith("}"):
                segment_name = segment[1: -1]
                route_template += f"/(?P<{segment_name}>[^/]+)"
            else:
                route_template += f"/{segment}"
        route_re = re.compile(f"^{route_template}$")
        self.routes_by_method[method][name] = route_re, handler
        self.names.add(name)
        # log
        
    def lookup(self, method, path):
        """Find handler function based on method(default='GET') and url path

        Args:
            method (str): HTTP method, default is 'GET'
            path (str): url path

        Returns:
            handler: bussinese logic function object,
                parameters: 
                    request, 
                    [option]: a dict include varable and value of varable
                return: 
                    response
        """
        for route_re, handler in self.routes_by_method[method].values():
            match = route_re.match(path)
            if match is not None:
                params = match.groupdict() # like: {"user_name": "Jack"}
                # log
                return functools.partial(handler, **params) # extended parameters
        # log
        return None

