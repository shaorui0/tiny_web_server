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


def server_static(path, sock):
    if path == '/':
        path = '/index.html'

    abspath = os.path.normpath(os.path.join(SERVER_ROOT, path.lstrip("/")))
    if not abspath.startswith(SERVER_ROOT):
        # sock.sendall(NOT_FOUND_RESPONSE)
        response = Response("404 Not Found", content="Not Found")
        response.send(client_sock)
        return
        
    try:
        with open(abspath, 'rb') as f:
            stat = os.fstat(f.fileno())
            content_type, encoding = mimetypes.guess_type(abspath)

            if content_type is None:
                content_type = "application/octet-stream"
            if encoding is not None:
                content_type += f"; charset={encoding}"

            # response_headers = FILE_RESPONSE_TEMPLATE.format(
            #     content_type=content_type,
            #     content_length=stat.st_size,
            # ).encode("ascii")
            
            response = Response("200 OK", body=f) # 服务器发送什么内容到客户端
            response.headers.add("content-type", content_type)
            # TODO content_length
            response.send(client_sock)


            # sock.sendall(response_headers)
            # sock.sendfile(f)
    except FileNotFoundError:
        # sock.sendall(NOT_FOUND_RESPONSE)
        response = Response("404 Not Found", content="Not Found")
        response.send(client_sock)
        return

with socket.socket() as server_sock:
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(0)
    print(f"Listening on {HOST}:{PORT}...")
    while True:
        client_sock, client_addr = server_sock.accept()
        print(f"New connection from {client_addr}.")
        with client_sock:
            try: # Try not to crash the server
                request = Request.from_socket(client_sock)
                try:
                    content_length = int(request.headers.get("content-length", "0"))
                except ValueError:
                    content_length = 0
                
                if content_length:
                    body = request.body.read(content_length)
                    print("Request body", body)

                if request.method != "GET":
                    # client_sock.sendall(METHOD_NOT_ALLOWED_RESPONSE)
                    response = Response("405 Method Not Allowed", content="Method Not Allowed")
                    response.send(client_sock)
                    continue
                
                server_static(request.path, client_sock)
            except Exception as e:
                print(f"Failed to parse request: {e}")
                # client_sock.sendall(BAD_REQUEST_RESPONSE)
                response = Response("400 Bad Request", content="Bad Request")
                response.send(client_sock)