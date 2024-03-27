from datetime import datetime
import hashlib

def log(who=1, message=""):
    fname = "1_echo_server/practice/logs/server_log.log" if who == 1 else "1_echo_server/practice/logs/client_log.log"
    with open(fname, "a") as file:
        file.write(f"{datetime.now()}| {message}\n")

def hash_password(user, password):
    password = user[0] + password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    return hashed_password

