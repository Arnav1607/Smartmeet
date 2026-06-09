import os, base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def get_key():
    key_hex = os.getenv('ENCRYPTION_KEY')
    if not key_hex:
        raise ValueError('ENCRYPTION_KEY not set in environment')
    return bytes.fromhex(key_hex)

def encrypt(plaintext: str) -> dict:
    """Encrypt text with AES-256-GCM. Returns {ciphertext_b64, iv_b64}."""
    key = get_key()
    iv = os.urandom(12)             # 96-bit nonce for GCM
    aesgcm = AESGCM(key)
    ct = aesgcm.encrypt(iv, plaintext.encode(), None)
    return {
        'ciphertext': base64.b64encode(ct).decode(),
        'iv': base64.b64encode(iv).decode()
    }

def decrypt(ciphertext_b64: str, iv_b64: str) -> str:
    """Decrypt AES-256-GCM ciphertext back to plaintext."""
    key = get_key()
    aesgcm = AESGCM(key)
    ct = base64.b64decode(ciphertext_b64)
    iv = base64.b64decode(iv_b64)
    return aesgcm.decrypt(iv, ct, None).decode()
