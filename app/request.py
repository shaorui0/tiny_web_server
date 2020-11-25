import io
import socket
import typing

from collections import defaultdict

from .headers import Headers

# 上面的全局函数还是不太好
# body如何获取数据，什么样的接口？
# 这里，还有个“技能点、决策点、精明点、闪光点，栈上buffer，预先填充，recv一次读取一个chunck，有些数据保存在栈上，后面再过来数据接在后面（这也为后面的非阻塞IO提供了思路，当前读了多少，但是我不能一直等吧，可能里面就返回了，但是此时过来了一部分）”
# buffer在这里类似一个滑动窗口 TODO 这个要自己实现，感觉是常用场景 

class BodyReader(io.IOBase): # TODO
    # 栈上buffer，保存part数据
    def __init__(self, sock, buff, buf_size=16_384):
        self._sock = sock
        self._buff = buff
        self._buf_size = buf_size
    
    def readable(self):
        return True # TODO 后面可能有用

    # 一个接口，用与进行read(n_byte)
    def read(self, n):
        while len(self._buff) < n: # 当数据不够一次read(n)
            data = self._sock.recv(self._buf_size)
            if not data: # TODO diff not a and a is None
                break
            self._buff += data

        ret, self._buff = self._buff[:n], self._buff[n:]
        return ret

class Request(typing.NamedTuple): # TODO
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
