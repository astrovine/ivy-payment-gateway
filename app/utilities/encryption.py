import base64
import hashlib
from cryptography.fernet import Fernet
from .config import settings
from .logger import setup_logger

logger = setup_logger(__name__)


def _get_fernet_key() -> bytes:
    key_bytes = settings.SECRET_KEY.encode()
    hashed = hashlib.sha256(key_bytes).digest()
    return base64.urlsafe_b64encode(hashed)


_fernet = None


def get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        _fernet = Fernet(_get_fernet_key())
    return _fernet


def encrypt_value(plaintext: str) -> str:
    if not plaintext:
        return plaintext
    try:
        fernet = get_fernet()
        encrypted = fernet.encrypt(plaintext.encode())
        return encrypted.decode()
    except Exception as e:
        logger.error(f"Encryption failed: {e}")
        raise ValueError("Failed to encrypt value")


def decrypt_value(ciphertext: str) -> str:
    if not ciphertext:
        return ciphertext
    try:
        fernet = get_fernet()
        decrypted = fernet.decrypt(ciphertext.encode())
        return decrypted.decode()
    except Exception as e:
        logger.error(f"Decryption failed: {e}")
        raise ValueError("Failed to decrypt value")


def is_encrypted(value: str) -> bool:
    if not value:
        return False
    try:
        fernet = get_fernet()
        fernet.decrypt(value.encode())
        return True
    except Exception:
        return False
