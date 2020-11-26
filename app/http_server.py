import os
import io
import socket
import typing
import mimetypes

from queue import Queue, Empty
from threading import Thread

from request import Request
from response import Response

SERVER_ROOT = 'www'


def server_static(sock, path):
    if path == '/':
        path = '/index.html'

    abspath = os.path.normpath(os.path.join(SERVER_ROOT, path.lstrip("/")))
    if not abspath.startswith(SERVER_ROOT):
        response = Response("404 Not Found", content="Not Found")
        response.send(sock)
        return
        
    try:
        with open(abspath, 'rb') as f:
            stat = os.fstat(f.fileno())
            content_type, encoding = mimetypes.guess_type(abspath)

            if content_type is None:
                content_type = "application/octet-stream"
            if encoding is not None:
                content_type += f"; charset={encoding}"

            response = Response("200 OK", body=f)
            response.headers.add("content-type", content_type)
            response.send(sock)
    except FileNotFoundError:
        response = Response("404 Not Found", content="Not Found")
        response.send(sock)
        return

class HTTPServer:
    def __init__(self, host="127.0.0.1", port=9000, worker_count=16):
        self.host = host
        self.port = port
        self.worker_count = worker_count
        self.worker_backlog = worker_count * 8
        self.connection_queue = Queue(self.worker_backlog)
    
    def server_forever(self):
        workers = []
        for _ in range(self.worker_count):
            worker = HTTPWorker()
            worker.start()
            workers.append(worker)

        with socket.socket() as server_sock:
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind((self.host, self.port))
            server_sock.listen(0)
            print(f"Listening on {self.host}:{self.port}...")
            while True:
                try:
                    self.connection_queue.put(server_sock.accept())
                except KeyboardInterrupt:
                    break

        for worker in workers:
            worker.stop()

        for worker in workers:
            worker.join(timeout=30)


class HTTPWorker(Thread):
    def __init__(self, connection_queue):
        self.connection_queue = connection_queue
        self.running = False

    def run(self):
        self.running = True
        while self.running:
            try:
                client_sock, client_addr = self.connection_queue.get(timeout=1) 
            except Empty:
                continue
            
            try:
                self._handle_client(client_sock, client_addr)
            except Exception as e:
                print(f"Unhandled error: {e}")
                continue
            finally:
                self.connection_queue.task_done()

    def _handle_client(self, client_sock, client_addr):
        with client_sock:
            try:
                request = Request.from_socket(client_sock)
                # TODO 100 continue

                try:
                    content_length = int(request.headers.get("content-length", "0"))
                except ValueError:
                    content_length = 0
                
                if content_length:
                    body = request.body.read(content_length)
                    print("Request body", body)

                if request.method != "GET":
                    response = Response("405 Method Not Allowed", content="Method Not Allowed")
                    response.send(client_sock)
                    return
                
                server_static(client_sock, request.path)
            except Exception as e:
                print(f"Failed to parse request: {e}")
                response = Response("400 Bad Request", content="Bad Request")
                response.send(client_sock)

server = HTTPServer()
server.server_forever()