import socket
from datetime import datetime
from functions import *

sock = socket.socket()
log(1, "Server is activated")
port = str(input("Введите номер порта: "))
port = int(port) if len(port) > 3 else 9090
while True:
	try:
		sock.bind(("", port))
		print(f"listening on port {port}")
		break
	except OSError:
		print(f"port is busy. trying {port+1}")
		port += 1
while True:
	try:
		sock.listen(0)
		log(1, f"listening on port {port}")
		conn, addr = sock.accept()
		log(1, f"got connection from {addr[0]}:{addr[1]}")

		msg = ''

		while True:
			data = conn.recv(1024)
			if not data:
				break
			log(1, f"got message from {addr[0]}:{addr[1]}")
			msg += data.decode()
			conn.send(data)
			log(1, f"send message to {addr[0]}:{addr[1]}")
			print(msg)
	except ConnectionResetError:
		continue

	#conn.close()
