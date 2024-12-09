from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os

class SecurityManager:
    def __init__(self):
        self.key = None
        self.fernet = None

    def generate_key(self, password: str, salt: bytes = None) -> bytes:
        """Generate a key from password."""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.key = key
        self.fernet = Fernet(key)
        return salt

    def encrypt_data(self, data: str) -> bytes:
        """Encrypt string data."""
        if not self.fernet:
            raise ValueError("Key not initialized. Call generate_key first.")
        return self.fernet.encrypt(data.encode())

    def decrypt_data(self, encrypted_data: bytes) -> str:
        """Decrypt encrypted data."""
        if not self.fernet:
            raise ValueError("Key not initialized. Call generate_key first.")
        return self.fernet.decrypt(encrypted_data).decode()

    def encrypt_file(self, file_path: str) -> bool:
        """Encrypt a file."""
        try:
            with open(file_path, 'rb') as file:
                file_data = file.read()
            encrypted_data = self.fernet.encrypt(file_data)
            with open(file_path + '.encrypted', 'wb') as file:
                file.write(encrypted_data)
            return True
        except Exception as e:
            print(f"Error encrypting file: {e}")
            return False
