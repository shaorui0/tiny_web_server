import socket

HOST = "127.0.0.1"
PORT = 9000

# response will be parsed by browser and print content of body(html).
RESPONSE = b"""\
HTTP/1.1 200 OK
Content-type: text/html
Content-length: 15

<h1>Hello!</h1>""".replace(b"\n", b"\r\n")

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


with socket.socket() as server_sock:
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(0) # 只处理一个链接（TODO test）
    print(f"Listening on {HOST}:{PORT}...")
    while True:
        client_sock, client_addr = server_sock.accept()
        print(f"New connection from {client_addr}.")
        with client_sock:
            for cur_line in iter_lines(client_sock):
                print(cur_line)
            client_sock.sendall(RESPONSE) # client will parse RESPONSE infomation

