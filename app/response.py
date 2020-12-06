import io
import os
import socket

from headers import Headers

class Response:
    """An HTTP response.

    Parameters:
      status: The resposne status line (eg. "200 OK").
      headers: The response headers.
      body: A file containing the response body.
      content: A string representing the response body.  If this is
        provided, then body is ignored.
      encoding: An encoding for the content, if provided.
    """
    def __init__(
            self, 
            status: str, 
            headers=None, 
            body=None,
            content=None,
            encoding: str = "utf-8"
        ):
        self.status = status.encode()
        self.headers = headers or Headers()
        
        if content:
            self.body = io.BytesIO(content.encode(encoding))
        elif body is None:
            self.body = io.BytesIO()
        else:
            self.body = body
    
    def send(self, sock: socket.socket) -> None:
        """Write this response to a socket.
        """
        content_length = self.headers.get("content-length")
        if content_length is None:
            try:
                body_stat = os.fstat(self.body.fileno())
                content_length = body_stat.st_size
            except OSError:
                self.body.seek(0, os.SEEK_END)
                content_length = self.body.tell()
                self.body.seek(0, os.SEEK_SET)

            if content_length > 0:
                self.headers.add("content-length", content_length)

        headers = b"HTTP/1.1 " + self.status + b"\r\n"
        for header_name, header_value in self.headers:
            headers += f"{header_name}: {header_value}\r\n".encode()
            # log

        sock.sendall(headers + b"\r\n")
        if content_length > 0:
            try:
                sock.sendfile(self.body)
                # log
            except:
                # log
                sock.sendfile(self.body) # TODO may raise BrokenPipe
