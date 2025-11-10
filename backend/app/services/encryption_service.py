import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", "your-encryption-key")

def encrypt_data(plaintext: str, key: str) -> str:
    """Encrypts data using AES-256-GCM."""
    f = Fernet(key.encode())
    return f.encrypt(plaintext.encode()).decode()

def decrypt_data(ciphertext: str, key: str) -> str:
    """Decrypts data using AES-256-GCM."""
    f = Fernet(key.encode())
    return f.decrypt(ciphertext.encode()).decode()

def generate_master_key() -> str:
    """Generates a 32-byte random key."""
    return Fernet.generate_key().decode()

def derive_key_from_password(password: str, salt: str) -> str:
    """Derives a key from a password and salt using PBKDF2."""
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt.encode(),
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key.decode()
