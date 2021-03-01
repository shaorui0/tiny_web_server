import socket, select
import threading

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serversocket.bind(('0.0.0.0', 8080))
serversocket.listen(100) # TODO 
serversocket.setblocking(0)

epoll = select.epoll()
epoll.register(serversocket.fileno(), select.EPOLLIN)


# print(threading.get_ident())

class EventLoop:
    """
    1. 创建 EventLoop 的是 IO thread，主要的功能是运行事件循环
    """
    def __init__(self):
        self.tid_ = threading.get_ident() # TODO
        self.looping_ = False


    def loop(self):
        """
        loop 里面做什么事情？
        """
        # looping
        assert self.looping_ is False
        self.assert_in_loop_thread()
        # in thread
        # set looping status
        self.looping_ == True
        epoll.poll(1)


    def assert_in_loop_thread(self):
        if not self.is_in_loop_thread():
            self._assert_not_in_loop_thread()

    def is_in_loop_thread(self):
        return  self.tid_ == threading.get_ident()
    
    def _assert_not_in_loop_thread(self):
        # log
        print("_assert_not_in_loop_thread: {}, {}".format(self.tid_, threading.get_ident()))