import re
from collections import OrderedDict, defaultdict

class Router:
    def __init__(self):
        self.routes_by_method = defaultdict(OrderedDict)
        self.names = set()
        
    def add_router(self, name, method, path, handler):
        assert path.startswith("/"), "paths must start with '/'"
        if name in self.names:
            raise ValueError(f"A route named {name} already exists.")
        
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
        
    def lookup(self, method, path):
        for route_re, handler in self.routes_by_method[method].values():
            match = route_re.match(path)
            if match is not None:
                params = match.groupdict()
                import functools
                return functools.partial(handler, **params)
        return None

