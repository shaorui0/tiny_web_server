import socket, select
import threading

class Channel:
    """
    1. 每个 channel 只负责一个 fd 的 IO 事件（read/write...）分发
        - 但是不拥有这个 fd （close不归它管）
        - 不同的事件分发成不同的 callback
        - 用户不直接使用 Channel
    """
    kNoneEvent = 0
    kReadEvent = select.EPOLLIN
    kReadEvent = select.EPOLLOUT

    def __init__(self, loop, fd):
        self.loop_ = loop
        self.fd_ = fd

        self.event_ = 0 # channel 关心的事件（bit_pattern）
        self.revent_ = 0 # 目前活跃的事件（bit_pattern）

        self.index_ = -1

        self.read_callback = None
        self.write_callback = None
        self.error_callback = None

    def handler_event(self):
        """
        loop.loop => channel.handler_event
        回调的使用，在这里体现出来

        这里是给业务逻辑留出来的接口
        """
        if self.revent_ & EPOLLERR:
            if self.error_callback:
                self.error_callback()
        if self.revent_ & (select.EPOLLIN | select.EPOLLPRI |select.EPOLLRDHUP):
            if self.read_callback:
                self.read_callback() 
        if self.revent_ & select.EPOLLOUT:
            if self.write_callback:
                self.write_callback()
        

    def update(self):
        """
        loop.update_channel => poller.update_channel
        """
        self.loop_.updateChannel(self) # TODO 这里传递self的含义

    def is_none_event(self):
        return self.event_ == self,kNoneEvent

    def set_revents(self, revent):
        self.revent_ = revent

    def set_idx(self, idx):
        self.index_ = idx
    
    def set_fd(self, fd):
        self.fd_ = fd

    def index(self, index_):
        return self.index_

    def fd(self):
        return self.fd_