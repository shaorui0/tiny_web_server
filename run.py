import socket

HOST = "127.0.0.1"
PORT = 9000

# response
RESPONSE = b"""\
HTTP/1.1 200 OK
Content-type: text/html
Content-length: 15

<h1>Hello!</h1>""".replace(b"\n", b"\r\n") # TODO b-string

with socket.socket() as server_sock:
    # set some config: reuse (TODO check what is reuse, why need this)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(0) # 只处理一个链接（TODO test）
    print(f"Listening on {HOST}:{PORT}...")
    while True:
        client_sock, client_addr = server_sock.accept()
        print(f"New connection from {client_addr}.")
        with client_sock:
            client_sock.sendall(RESPONSE)
