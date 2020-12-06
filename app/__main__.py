import functools
import json
import sys
import os
import mimetypes
from typing import Callable, Tuple, Union

from application import Application
from request import Request
from response import Response
from http_server import HTTPServer, serve_static

USERS = [
    {"id": 1, "name": "Jim"},
    {"id": 2, "name": "Bruce"},
    {"id": 3, "name": "Dick"},
]

SERVER_ROOT = "www"

###### helper functions #######################
def jsonresponse(handler: Callable[..., Union[dict, Tuple[str, dict]]]) -> Callable[..., Response]:
    @functools.wraps(handler)
    def wrapper(*args, **kwargs):
        result = handler(*args, **kwargs)
        if isinstance(result, tuple):
            status, result = result
        else:
            status, result = "200 OK", result

        # form a complete http response
        response = Response(status=status)
        response.headers.add("content-type", "application/json")
        response.body.write(json.dumps(result).encode())
        
        return response
    return wrapper

def wrap_auth(handler):
    def auth_handler(request):
        authorization = request.headers.get("authorization", "")
        if authorization.startswith("Bearer ") and authorization[len("Bearer "):] == "opensesame":
            return handler(request)
        return Response(status="403 Forbidden", content="Forbidden!")
    return auth_handler

##############################################

app = Application()

############ register ########################

@app.route("/users")
@jsonresponse
def get_users(request):
    return {"users": USERS}


@app.route("/users/{user_id}")
@jsonresponse
def get_user(request, user_id):
    try:
        return {"user": USERS[int(user_id)]}
    except (IndexError, ValueError):
        return "404 Not Found", {"error": "Not found"}

@app.route("/hello")
@wrap_auth
def hello(request):
    return Response(content="Hello!")

@app.route("/{static}")
def server_static(request, static):
    path = request.path
    if request.path == '/index':
        path = '/index.html'

    abspath = os.path.normpath(os.path.join(SERVER_ROOT, path.lstrip("/")))
    if not abspath.startswith(SERVER_ROOT):
        return Response("404 Not Found", content="Not Found")

    try:
        content_type, encoding = mimetypes.guess_type(abspath)

        if content_type is None:
            content_type = "application/octet-stream"
        if encoding is not None:
            content_type += f"; charset={encoding}"

        body_file = open(abspath, 'rb')
        response = Response(status="200 OK", body=body_file)

        response.headers.add("content-type", content_type)
        return response
    except FileNotFoundError:
        return Response("404 Not Found", content="Not Found")

##############################################

def main():
    server = HTTPServer()
    server.mount("", app)
    
    server.server_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())