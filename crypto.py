"""
Securely store data in an encrypted file

generate_key()
my_key = load_key()
encrypt_and_write("protected_data.bin", "This is sensitive information.", my_key)
secret_message = read_and_decrypt("protected_data.bin", my_key)
print(secret_message)

"""
from cryptography.fernet import Fernet

KEY_FILE = "secret.key"

# Generate a key and save it to a file
def generate_key():
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as key_file:
        key_file.write(key)

# Load the previously generated key
def load_key():
    return open(KEY_FILE, "rb").read()

def encrypt_and_write(filename, data, key):
    f = Fernet(key)
    # Ensure data is in bytes (e.g., encode a string)
    encoded_data = data.encode()
    encrypted_data = f.encrypt(encoded_data)
    
    with open(filename, "wb") as file:
        file.write(encrypted_data)

def read_and_decrypt(filename, key):
    f = Fernet(key)
    with open(filename, "rb") as file:
        encrypted_data = file.read()
    
    decrypted_data = f.decrypt(encrypted_data)
    return decrypted_data.decode()

