# gps_bt_test.py
import socket

server_sock = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
server_sock.bind(("00:00:00:00:00:00", 1))
server_sock.listen(1)

print("대기 중... (채널 1)")
client_sock, client_info = server_sock.accept()
print(f"연결됨: {client_info}")

buffer = ""
while True:
    data = client_sock.recv(1024)
    if not data:
        break
    buffer += data.decode("utf-8", errors="ignore")
    while "\n" in buffer:
        line, buffer = buffer.split("\n", 1)
        print(f"받음: {line.strip()}")

client_sock.close()
server_sock.close()
