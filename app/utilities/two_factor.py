import base64
import io
import pyotp
import qrcode
from .logger import setup_logger
from .encryption import encrypt_value, decrypt_value

logger = setup_logger(__name__)


def generate_totp_secret() -> str:
    secret = pyotp.random_base32()
    return encrypt_value(secret)


def get_totp_uri(email: str, encrypted_secret: str, issuer: str = "IvyPayments") -> str:
    secret = decrypt_value(encrypted_secret)
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=email, issuer_name=issuer)


def generate_qr_code_base64(email: str, encrypted_secret: str, issuer: str = "IvyPayments") -> str:
    uri = get_totp_uri(email, encrypted_secret, issuer)
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    
    return base64.b64encode(buffer.getvalue()).decode()


def verify_totp(encrypted_secret: str, code: str) -> bool:
    if not encrypted_secret or not code:
        return False
    
    try:
        secret = decrypt_value(encrypted_secret)
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)
    except Exception as e:
        logger.error(f"TOTP verification failed: {e}")
        return False


def get_current_totp(encrypted_secret: str) -> str:
    secret = decrypt_value(encrypted_secret)
    totp = pyotp.TOTP(secret)
    return totp.now()
