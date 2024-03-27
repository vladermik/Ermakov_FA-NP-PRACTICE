import socket
from time import sleep
from functions import *

sock = socket.socket()
sock.setblocking(1)
port = str(input("Введите номер порта: "))
port = port if len(port) > 3 else 9090
host = str(input("Введите имя хоста: "))
host = host if len(host) > 5 else "127.0.0.1"
sock.connect((host, int(port)))
log(2, f"connected with {host}:{port}")

while True:
    if port == 2020 and host == "127.0.0.1":
        data = sock.recv(1024).decode()
        print(data)
        msg = str(input())
        sock.send(msg.encode)
        data = sock.recv(1024).decode()
        print(data)
        break
    msg = input()
    if msg.lower() != "exit":
        sock.send(msg.encode())
        log(2, f"data was sent to {host}:{port}")
        data = sock.recv(1024)
        log(2, f"data was received back from {host}:{port}")
        print(data.decode())
    else:
        break
sock.close()
log(2, f"connection with {host}:{port} closed")


