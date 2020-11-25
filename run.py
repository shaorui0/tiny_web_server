import socket
import typing

HOST = "127.0.0.1"
PORT = 9000

# response will be parsed by browser and print content of body(html).
# 200
RESPONSE = b"""\
HTTP/1.1 200 OK
Content-type: text/html
Content-length: 15

<h1>Hello!</h1>""".replace(b"\n", b"\r\n")

# 400
BAD_REQUEST_RESPONSE = b"""\
HTTP/1.1 400 Bad Request
Content-type: text/plain
Content-length: 11

Bad Request""".replace(b"\n", b"\r\n")


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
                client_sock.sendall(RESPONSE)
            except Exception as e:
                print(f"Failed to parse request: {e}")
                client_sock.sendall(BAD_REQUEST_RESPONSE)