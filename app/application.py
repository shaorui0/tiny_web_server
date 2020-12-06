from .router import Router
from .request import Request
from .response import Response

class Application:
    def __init__(self):
        self.router = Router()

    def __call__(self, requst):
        handler = self.router.lookup(requst.method, requst.path)
        if handler is None:
            return Response("404 Not Found", content="Not Found")
        return handler(requst)
    
    def route(self,
            path, 
            method = "GET",
            name = None,
    ):
        """add a pair(name-path-method, handler) to router

        Args:
            path (str): path
            method (str, optional): method. Defaults to "GET".
            name (str, optional): name. Defaults to None.
        """
        def decorator(handler):
            self.add_router(path, handler, method, name) 
            return handler
        return decorator
    
    def add_router(self,
            path, 
            handler, 
            method = "GET",
            name = None,
    ):
        self.router.add_router(name or handler.__name__, method, path, handler)
