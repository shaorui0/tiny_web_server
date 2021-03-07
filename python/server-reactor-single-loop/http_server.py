import select
import os
import io
import socket
import typing
import mimetypes

from queue import Queue, Empty
import threading

from request import Request
from response import Response
from log import with_log, log

def serve_static(server_root):
    """serve http static content

    Args:
        server_root (str): http static path
    """
    def handler(request):
        path = request.path
        if request.path == '/':
            path = '/index.html'

        abspath = os.path.normpath(os.path.join(server_root, path.lstrip("/")))
        
        if not abspath.startswith(server_root):
            log.info(f"[404 Not Found] url error, [{server_root}]")
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
            log.error(f"[404 Not Found] there is not exist the path [{abspaths}]")
            return Response("404 Not Found", content="Not Found")
    
    return handler


@with_log   
class HTTPServer:
    def __init__(self, host="127.0.0.1", port=9000):
        self.host = host
        self.port = port
        self.connections = {}
        self.handlers = []
        self.handlers_fd = {}
        self.epoll = select.epoll()
        self.requests = {}
        self._init_epoll()
    
    def _init_epoll(self):
        self.serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.serversocket.bind((self.host, self.port))
        self.serversocket.listen(100) # TODO 
        self.serversocket.setblocking(0)
        self.epoll.register(self.serversocket.fileno(), select.EPOLLIN)
        self.handlers_fd[self.serversocket.fileno()] = self.handle_accept
    
    def handle_accept(self, fileno, event):
        connection, address = self.serversocket.accept()
        connection.setblocking(0)
        self.epoll.register(connection.fileno(), select.EPOLLIN)
        self.connections[connection.fileno()] = connection
        self.handlers_fd[connection.fileno()] = self.handle_request

    def handle_request(self, fileno, event):
        client_sock = self.connections[fileno]
        if event & select.EPOLLIN:
            try:
                request = self.handle_client_read(client_sock)
                self.requests[fileno] = request
            except Exception:
                self.epoll.modify(fileno, select.EPOLLOUT)
                response = Response(status="400 Bad Request", content="Bad Request")
                response.send(client_sock)
                return
        
            self.epoll.modify(fileno, select.EPOLLOUT)

            if request.method != "GET":
                response = Response("405 Method Not Allowed", content="Method Not Allowed")
                response.send(client_sock)
                self.log.error(f"[405 Method Not Allowed] {request.method}")
                return

        elif event & select.EPOLLOUT:
            self.handle_client_write(client_sock, self.requests[fileno])
            # sendall and close, 需要有一个 buffer 来管理
            self.epoll.modify(fileno, 0)
            self.connections[fileno].shutdown(socket.SHUT_RDWR) # 读到0，优雅关闭（让 client 先关）
            del self.connections[fileno]
        elif event & select.EPOLLHUP:
            self.epoll.unregister(fileno)
            self.connections[fileno].close()
            del self.connections[fileno]

    def mount(self, path_prefix, handler):
        """Mount a request handler at a particular path.  Handler
        prefixes are tested in the order that they are added so the
        first match "wins".
        """
        self.handlers.append((path_prefix, handler))
        self.log.info("mounted a request handler, path: [{path_prefix}]")
        
    def server_forever(self):
        try:
            self.log.info(f"Listening on {self.host}:{self.port}...")
            while True:
                try:
                    events = self.epoll.poll(1)  # 1 ms
                    for fileno, event in events:
                        callback = self.handlers_fd[fileno]
                        callback(fileno, event)
                except KeyboardInterrupt:
                    self.log.exception(f"[KeyboardInterrupt] server has been stopped")
                    break
        finally:
            self.serversocket.close()
            self.epoll.unregister(self.serversocket.fileno())
            self.epoll.close()

    
    def handle_client_read(self, client_sock: socket.socket):
        request = Request.from_socket(client_sock)
        return request

    def handle_client_write(self, client_sock: socket.socket, request):
        for path_prefix, handler in self.handlers:
            if request.path.startswith(path_prefix):
                try:
                    request = request._replace(path=request.path[len(path_prefix):])
                    response = handler(request) # business logic
                    response.send(client_sock)
                except Exception as e:
                    response = Response(status="500 Internal Server Error", content="Internal Error")
                    response.send(client_sock)
                    self.log.error(f"[500 Internal Server Error] [{e}]")
                finally:
                    break
        else:
            response = Response(status="404 Not Found", content="Not Found")
            response.send(client_sock)
            log.error(f"[404 Not Found] there is not exist the path [{abspaths}]")
            

def app(request: Request):
    """[For test, return Hello whenever you enter 'localhost:9000/test']

    Args:
        request (Request): [http request]

    Returns:
        [Response]: [http response]
    """
    return Response(status="200 OK", content="Hello!")

def wrap_auth(handler):
    def auth_handler(request):
        authorization = request.headers.get("authorization", "")
        if authorization.startswith("Bearer ") and authorization[len("Bearer "):] == "opensesame":
            # log
            return handler(request)
        # log
        return Response(status="403 Forbidden", content="Forbidden!")
    # log
    return auth_handler

