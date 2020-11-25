import os
import socket
import typing
import mimetypes

HOST = "127.0.0.1"
PORT = 9000
SERVER_ROOT = 'www'

# request status code

# 200
FILE_RESPONSE_TEMPLATE = """\
HTTP/1.1 200 OK
Content-type: {content_type}
Content-length: {content_length}

""".replace("\n", "\r\n")

# 400
BAD_REQUEST_RESPONSE = b"""\
HTTP/1.1 400 Bad Request
Content-type: text/plain
Content-length: 11

Bad Request""".replace(b"\n", b"\r\n")

# 404, cannot find index file
NOT_FOUND_RESPONSE = b"""\
HTTP/1.1 404 Not Found
Content-type: text/plain
Content-length: 9

Not Found""".replace(b"\n", b"\r\n")

# 405, Method Not Allowed
METHOD_NOT_ALLOWED_RESPONSE = b"""\
HTTP/1.1 405 Method Not Allowed
Content-type: text/plain
Content-length: 17

Method Not Allowed""".replace(b"\n", b"\r\n")

def iter_lines(a_socket, buf_size=16_384):
    buf = b""

    while True: # the content that readed from socket will greater than buf_size, so use while True
        data = a_socket.recv(buf_size)
        if not data:
            return b""
        
        buf += data
        while True: # read line split by CRLF
            try:
                i = buf.index(b"\r\n")
                cur_line, buf = buf[:i], buf[i+2:]
                if not cur_line:
                    return buf
                yield cur_line 
            except IndexError:
                break

def iter_lines(sock: socket.socket, bufsize: int = 16_384) -> typing.Generator[bytes, None, bytes]:
    buff = b""
    while True:
        data = sock.recv(bufsize)
        if not data:
            return b""

        buff += data
        while True:
            try:
                i = buff.index(b"\r\n")
                line, buff = buff[:i], buff[i + 2:]
                if not line:
                    return buff

                yield line
            except IndexError:
                break


def server_static(path, sock):
    if path == '/':
        path = '/index.html'

    abspath = os.path.normpath(os.path.join(SERVER_ROOT, path.lstrip("/")))
    if not abspath.startswith(SERVER_ROOT):
        sock.sendall(NOT_FOUND_RESPONSE)
        return
        
    try:
        with open(abspath, 'rb') as f:
            stat = os.fstat(f.fileno())
            content_type, encoding = mimetypes.guess_type(abspath)

            if content_type is None:
                content_type = "application/octet-stream"
            if encoding is not None:
                content_type += f"; charset={encoding}"

            response_headers = FILE_RESPONSE_TEMPLATE.format(
                content_type=content_type,
                content_length=stat.st_size,
            ).encode("ascii")

            sock.sendall(response_headers)
            sock.sendfile(f)
    except FileNotFoundError:
        sock.sendall(NOT_FOUND_RESPONSE)
        return

class Request(typing.NamedTuple): # TODO
    method: str
    path: str
    headers: typing.Mapping[str, str]

    @classmethod
    def from_socket(cls, sock):
        lines = iter_lines(sock)
        try:
            request_line = next(lines).decode('ascii')
        except StopIteration:
            raise ValueError("Request line error.")

        try:
            method, path, _ = request_line.split(" ")
        except ValueError:
            raise ValueError(f"Malformed request line {request_line!r}.")

        headers = {}
        for line in lines:
            try:
                name, _, value = line.decode("ascii").partition(":")
                headers[name.lower()] = value.lstrip()
            except ValueError:
                raise ValueError(f"Malformed header line {line!r}.")
        
        return cls(method=method.upper(), path=path, headers=headers)

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
                print(request)

                if request.method != "GET":
                    client_sock.sendall(METHOD_NOT_ALLOWED_RESPONSE)
                    continue
                
                server_static(request.path, client_sock)
            except Exception as e:
                print(f"Failed to parse request: {e}")
                client_sock.sendall(BAD_REQUEST_RESPONSE)