import os
import io
import socket
import typing
import mimetypes
from request import Request
from response import Response

HOST = "127.0.0.1"
PORT = 9000
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
    def __init__(self, host="127.0.0.1", port=9000):
        self.host = host
        self.port = port
    
    def server_forever(self):
        with socket.socket() as server_sock:
            server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_sock.bind((self.host, self.port))
            server_sock.listen(0)
            print(f"Listening on {self.host}:{self.port}...")
            while True:
                client_sock, client_addr = server_sock.accept()
                print(client_sock, client_addr)

                self._handle_client(client_sock, client_addr)

    def _handle_client(self, client_sock, client_addr):
        with client_sock:
            try: # Try not to crash the server
                request = Request.from_socket(client_sock)
                print(request.headers._headers)
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