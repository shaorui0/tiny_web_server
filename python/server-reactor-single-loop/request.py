import io
import socket
import typing

from collections import defaultdict

from headers import Headers

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
    An HTTP request.

    Parameters:
      method: The request method line (eg. "GET").
      path: The request path.
      headers: A string representing the request body.
      body: A BodyReader reading content from socket.
    """
    method: str
    path: str
    headers: Headers
    body: BodyReader

    @classmethod
    def from_socket(cls, sock):
        """[Generate a http request from client socket]

        Args:
            sock ([socket.socket]): [a socket will be read]

        Raises:
            ValueError: [There is no http header]
            ValueError: [There is no eligible content about http header]
            ValueError: [The http body cannot be partition by ':']

        Returns:
            [Request]: [HTTP request(method, path, headers, body)]
        """
        lines = iter_lines(sock)
        try:
            # request head(method, path, http version)
            request_line = next(lines).decode('ascii')
        except StopIteration:
            raise ValueError("Request line error.")

        try:
            # log
            method, path, _ = request_line.split(" ")
        except ValueError:
            # log
            raise ValueError(f"Malformed request line {request_line!r}.")

        headers = Headers()
        buff = b""
        while True:
            try:
                line = next(lines)
            except StopIteration as e:
                # StopIteration.value contains the return value of the generator.
                # log
                buff = e.value
                break

            name, sep, value = line.decode("ascii").partition(":")
            headers.add(name, value.lstrip())
            if not sep and not value:
                # wrong format
                # log
                raise ValueError(f"Malformed header line {line!r}.")
        
        body = BodyReader(sock, buff=buff)
        # log
        return cls(method=method.upper(), path=path, headers=headers, body=body)

def iter_lines(sock: socket.socket, bufsize: int = 16_384):
    """
    Iterate the content recieved by socket, partition by CRLF('\\r\\n')
    
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
