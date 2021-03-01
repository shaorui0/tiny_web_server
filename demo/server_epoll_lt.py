import socket, select

EOL1 = b'\n\n'
EOL2 = b'\n\r\n'
response  = b'HTTP/1.0 200 OK\r\nDate: Mon, 1 Jan 1996 01:01:01 GMT\r\n'
response += b'Content-Type: text/plain\r\nContent-Length: 13\r\n\r\n'
response += b'Hello, world!'

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serversocket.bind(('0.0.0.0', 8080))
serversocket.listen(100) # TODO 
serversocket.setblocking(0)

epoll = select.epoll()
epoll.register(serversocket.fileno(), select.EPOLLIN)


try:
    connections = {}; requests = {}; responses = {}
    while True:
        events = epoll.poll(1)
        for fileno, event in events:
            # int, bit_pattern
            print("fileno, event: ", fileno, event)
            # 无非是通过epoll对不同的分类事件进行监听

            # add_new_connection
            if fileno == serversocket.fileno():
                # client_socker, address
                connection, address = serversocket.accept() # TODO 这里加入到阻塞队列中
                
                connection.setblocking(0)
                epoll.register(connection.fileno(), select.EPOLLIN)
                # 注册事件， index_fd => socket
                connections[connection.fileno()] = connection
                # 这里的request，response 设置为全局的吗？怎么处理
                requests[connection.fileno()] = b''
                responses[connection.fileno()] = response
            # add_read_event
            elif event & select.EPOLLIN:
                # 每次读多少？
                client_sock = connections[fileno]
                requests[fileno] += client_sock.recv(1024)
                print(">>> " + requests[fileno].decode()[:-2] + "\n")
                if EOL1 in requests[fileno] or EOL2 in requests[fileno]:
                    epoll.modify(fileno, select.EPOLLOUT) # request -> response
                    print('-'*40 + '\n' + requests[fileno].decode()[:-2])
            # add_write_event
            elif event & select.EPOLLOUT:
                # input: client_sock
                client_sock = connections[fileno]
                response_content = responses[fileno]
                byteswritten = client_sock.send(response_content) # 发送
                responses[fileno] = responses[fileno][byteswritten:] # 截断
                if len(responses[fileno]) == 0: # 如果发完
                    epoll.modify(fileno, 0)
                    client_sock.shutdown(socket.SHUT_RDWR) # 优雅关闭（让 client 先关）
            # close_connection
            elif event & select.EPOLLHUP:
                # input: fileno, self.connections（全局的？当前线程中的，能够）
                epoll.unregister(fileno)
                connections[fileno].close()
                del connections[fileno]
finally:
    epoll.unregister(serversocket.fileno())
    epoll.close()
    serversocket.close()
