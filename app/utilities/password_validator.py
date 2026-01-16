import re
from typing import Optional
from .logger import setup_logger

logger = setup_logger(__name__)


class PasswordValidationError(Exception):
    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def validate_password_strength(
    password: str,
    min_length: int = 8,
    require_uppercase: bool = True,
    require_lowercase: bool = True,
    require_digit: bool = True,
    require_special: bool = True,
    check_common: bool = True
) -> tuple[bool, list[str]]:
    errors = []
    
    if len(password) < min_length:
        errors.append(f"Password must be at least {min_length} characters")
    
    if require_uppercase and not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    if require_lowercase and not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    if require_digit and not re.search(r'\d', password):
        errors.append("Password must contain at least one number")
    
    if require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\;\'`~]', password):
        errors.append("Password must contain at least one special character")
    
    if password.lower() in password.lower():
        repeated = re.search(r'(.)\1{3,}', password)
        if repeated:
            errors.append("Password cannot contain 4 or more repeated characters")
    
    return len(errors) == 0, errors


def get_password_strength_score(password: str) -> int:
    score = 0
    
    if len(password) >= 8:
        score += 1
    if len(password) >= 12:
        score += 1
    if len(password) >= 16:
        score += 1
    
    if re.search(r'[A-Z]', password):
        score += 1
    if re.search(r'[a-z]', password):
        score += 1
    if re.search(r'\d', password):
        score += 1
    if re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        score += 1

    
    return min(score, 10)
