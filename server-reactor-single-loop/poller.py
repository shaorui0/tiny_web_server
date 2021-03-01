import time 
from channel import Channel

class Poller:
    """
    IO multiplexing 的封装
    想象一下他是干什么的？
    1. 每次 epoll 会监听一个fd（也就是addr+port）
    2. 这个 poll 会产生很多事件（fds）
    3. 迭代处理（poller不处理，只是传递给channel）

    重点是数据结构是怎样的？
    """
    def __init__(self, loop):
        self.loop_ = loop
        self.poll_fd_list = list()# cache: events = epoll()
        # 所有关注的 fd，这个有意义吗？
        self.channel_map = dict() # key: fd
        # 通过fd 能找到channel，python 中能找到connection 吗

    def poll(self, timeout_ms):
        """
        产生一个时间
        timeout_ms: 
        """
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serversocket.bind(('0.0.0.0', 8080))
        serversocket.listen(100) # TODO 
        serversocket.setblocking(0)

        epoll = select.epoll()
        epoll.register(serversocket.fileno(), select.EPOLLIN)

        events = epoll.poll(timeout_ms / 1000)
        # TODO events -> channels
        ## 存在 或 不存在
        # 输入是 pollfd_list(包含所有的)，输出是 active_channels（仅仅是active的）
        # 本质是 read_fds, ready_fds
        len_events = len(events)
        now = time.time() 
        # for fileno, event in events:
        if len_events > 0:
            # active_channel_list 是什么样的格式？
            # events 可能有已知的，可能有未知的
            # 这里的功能就是在这里找到活跃的
            active_channel_list = self._fill_active_channels(events)
        elif len_events == 0:
            # log
            print("len_events == 0")
        else:
            # log
            print("len_events < 0")
        return now, active_channel_list

    
    def update_channel(self, channel):
        """
        分发给channel
        用来维护 poll_fd_list cache，把相关的channel加进去

        new connection
        """
        assert self._assert_in_loop_thread() is True
        if channel.index() < 0:
            # new connection
            assert channel.fd() not in self.channel_map
            
            self.poll_fd_list.append(channel)
            # 为了快速在 poll_fd_list 中找到channel，还设置了一个index
            channel.set_idx(len(self.poll_fd_list) - 1)
            self.channel_map[channel.fd(] = channel
        else:
            assert channel.fd() in self.channel_map
            assert self.channel_map[channel.fd()] is self.channel_map
            idx = channel.index()
            assert idx >=0 and idx < len(self.poll_fd_list)
            pollfd = self.poll_fd_list[idx]
            pollfd.events = channel.events
            pollfd.set_revents(0)
            if channel.is_none_event():
                pollfd.set_fd(-1)

    def _assert_in_loop_thread(self):
        # TODO
        pass
    
    def _fill_active_channels(self, events):
        """核心流程，主要是干什么的？
        """
        active_channel_list = list()
        for fileno, event in events:
            # 可能有已知的，可能有未知的，主要是根据数据结构进行检查
            channel = Channel()
            channel.fd( = fileno
            channel.set_revents()
            self.channel_map[fileno] = 
            active_channel_list.append()
        return active_channel_list

    