from router import Router
from request import Request
from response import Response

class Application:
    self.router = Router()

    def route(
        self,
        path, 
        method = "GET",
        name = None,
    ):
        pass
    
    def __call__(self, requst):
        handler = self.router.lookup(requst.method, requst.path)
        if handler is None:
            return Response("404 Not Found", content="Not Found")
        return handler(requst)