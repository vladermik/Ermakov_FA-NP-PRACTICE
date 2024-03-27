import hashlib

def hash_password(user, password):
    password = user[0] + password
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    return hashed_password