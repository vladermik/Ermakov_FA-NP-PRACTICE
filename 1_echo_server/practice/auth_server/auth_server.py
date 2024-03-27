import socket
from functions import *

sock = socket.socket()
sock.bind(("", 2020))
sock.listen(1)
conn, addr = sock.accept()
ip = addr[0]
with open(r"1_echo_server\practice\auth_server\users.txt", "r") as file:
	users = file.readlines()
	for el in users:
		print(el, len(el))
		ip1, user, stored_password = el.split(":")
		if ip1 == ip:
			conn.send(f"Здравствуйте, {user}!\nВведите пароль: ".encode())
			password = conn.recv(1024).decode()
			if hash_password(user, password) == stored_password.strip():
				conn.send(f"Аутентификация успешно пройдена!".encode())
			else:
				conn.send("Неверный пароль!".encode())
		break
	else:
		conn.send("Вас еще нету в системе\n Введите имя пользователя и пароль, разделив их пробелом: ".encode())
		user, password = conn.recv(1024).decode().split()
		print(user, password)
		password = hash_password(user, password)
		with open(r"1_echo_server\practice\auth_server\users.txt", "a") as f:
			f.write(f"{ip}:{user}:{password}\n")
		conn.send("Пользователь успешно создан!".encode())
conn.close()