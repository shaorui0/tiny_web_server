import io
import socket
import typing

from collections import defaultdict

from .headers import Headers

class BodyReader(io.IOBase):
    """
    buffer in stack, keep part of data that recv from socket, the data cannot be yield because of CRLF.
    """
    def __init__(self, sock, buff, buf_size=16_384):
        self._sock = sock
        self._buff = buff
        self._buf_size = buf_size
    
    def readable(self):
        return True

    def read(self, n):
        # when the data is not enough to read once
        while len(self._buff) < n:
            data = self._sock.recv(self._buf_size)
            if not data:
                break
            self._buff += data

        ret, self._buff = self._buff[:n], self._buff[n:]
        return ret

class Request(typing.NamedTuple):
    """
    Keep method, path, header(s) and body that parsed by HTTP request content
    """
    method: str
    path: str
    headers: Headers
    body: BodyReader

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

        headers = Headers()
        buff = b""
        while True:
            try:
                line = next(lines)
            except StopIteration as e:
                # StopIteration.value contains the return value of the generator.
                buff = e.value
                break
        
            try:
                name, value = line.decode("ascii").split(":")
                headers.add(name, value.lstrip())
            except ValueError:
                raise ValueError(f"Malformed header line {line!r}.")
        
        body = BodyReader(sock, buff=buff)
        return cls(method=method.upper(), path=path, headers=headers, body=body)

def iter_lines(sock: socket.socket, bufsize: int = 16_384) -> typing.Generator[bytes, None, bytes]:
    """
    Iterate the content recieved by socket, partition by CRLF('\r\n')
    
    Parameters:
        socket: a socket will be read 
        bufsize: read bufsize byte(s) each time from socket

    Return:
        line(yield or return): 
            yield complete line
            return part of line(no CRLF at the end) 
    """
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
            except ValueError:
                break
