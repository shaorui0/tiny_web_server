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
class HTTPWorker(threading.Thread):
    def __init__(self, connection_queue, handlers):
        super().__init__(daemon=True)
        self.connection_queue = connection_queue
        self.handlers = handlers # callback method based on http path
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            try:
                client_sock, client_addr = self.connection_queue.get(timeout=1)
            except Empty:
                # log
                continue
            
            try:
                self.handle_client(client_sock, client_addr)
                self.log.info("tid: [{}], client address: [{}]".format(threading.get_ident(), client_addr))
            except Exception as e:
                self.log.error(f"Unhandled error: {e}")
                continue
            finally:
                self.connection_queue.task_done()

    def handle_client(self, client_sock: socket.socket, client_addr: typing.Tuple[str, int]):
        with client_sock:
            try:
                request = Request.from_socket(client_sock)
            except Exception:
                response = Response(status="400 Bad Request", content="Bad Request")
                response.send(client_sock)
                return

            # Force clients to send their request bodies on every
            # request rather than making the handlers deal with this.
            
            # if "100-continue" in request.headers.get("expect", ""):
            #     response = Response(status="100 Continue")
            #     response.send(client_sock)
            
            # POST
            # if content_length:
            #     body = request.body.read(content_length)
            #     print("Request body", body)
            
            # GET
            if request.method != "GET":
                response = Response("405 Method Not Allowed", content="Method Not Allowed")
                response.send(client_sock)
                self.log.error(f"[405 Method Not Allowed] {request.method}")
                return
            

            for path_prefix, handler in self.handlers: # TODO dict
                if request.path.startswith(path_prefix):

                    try:
                        request = request._replace(path=request.path[len(path_prefix):])
                        response = handler(request) # logic of user defined
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
                log.info(f"[404 Not Found] there is not exist the path [{abspaths}]")

@with_log   
class HTTPServer:
    def __init__(self, host="127.0.0.1", port=9000, worker_count=16):
        self.host = host
        self.port = port
        self.worker_count = worker_count
        self.worker_backlog = worker_count * 8
        self.connection_queue = Queue(self.worker_backlog)
        self.handlers = []
    
    def mount(self, path_prefix, handler):
        """Mount a request handler at a particular path.  Handler
        prefixes are tested in the order that they are added so the
        first match "wins".
        """
        self.handlers.append((path_prefix, handler))
        self.log.info("mounted a request handler, path: [{path_prefix}]")
        
    def server_forever(self):
        workers = []
        for _ in range(self.worker_count):
            worker = HTTPWorker(self.connection_queue, self.handlers)
            worker.start()
            workers.append(worker)

        with socket.socket() as server_sock:
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind((self.host, self.port))
            server_sock.listen(0)
            self.log.info(f"Listening on {self.host}:{self.port}...")
            while True:
                try:
                    self.connection_queue.put(server_sock.accept())
                except KeyboardInterrupt:
                    self.log.exception(f"[KeyboardInterrupt] server has been stopped")
                    break

        for worker in workers:
            worker.stop()

        for worker in workers:
            worker.join(timeout=30)


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

