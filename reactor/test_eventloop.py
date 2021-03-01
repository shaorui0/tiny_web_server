import threading
from event_loop import EventLoop

def test():
    event_loop = EventLoop()
    event_loop.loop()



g_event_loop = EventLoop()
g_event_loop.loop()

def test2():
    def thread_function(loop):
        loop.loop()

    x = threading.Thread(target=thread_function, args=(g_event_loop,))
    x.start()
    x.join(timeout=30)

test() 
test2()