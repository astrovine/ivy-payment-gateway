from fastapi import HTTPException, status

class PaymentGatewayException(Exception):
    """Base exception for payment gateway"""
    def __init__(self, detail: str, code: str = "INTERNAL_ERROR"):
        self.detail = detail
        self.code = code
        super().__init__(self.detail)


class InvalidRequestError(PaymentGatewayException):
    def __init__(self, detail: str = "Invalid request"):
        super().__init__(detail, "INVALID_REQUEST")

class ResourceNotFoundError(PaymentGatewayException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(f"{resource} not found", "RESOURCE_NOT_FOUND")

class DatabaseError(PaymentGatewayException):
    def __init__(self, reason: str = ""):
        detail = f"Database error: {reason}" if reason else "A database error occurred"
        super().__init__(detail, "DATABASE_ERROR")

class ServiceUnavailableError(PaymentGatewayException):
    def __init__(self, service: str = "External service"):
        super().__init__(f"{service} is unavailable", "SERVICE_UNAVAILABLE")

class UserNotFoundError(ResourceNotFoundError):
    def __init__(self, detail: str = "User not found"):
        super().__init__(detail)

class DuplicateEmailError(PaymentGatewayException):
    def __init__(self):
        super().__init__("Email already exists", "DUPLICATE_EMAIL")

class UserCreationError(PaymentGatewayException):
    def __init__(self, reason: str = ""):
        detail = f"Failed to create user: {reason}" if reason else "Failed to create user"
        super().__init__(detail, "USER_CREATION_FAILED")

class InvalidCredentialsError(PaymentGatewayException):
    def __init__(self, detail: str = "Invalid email or password"):
        super().__init__(detail, "INVALID_CREDENTIALS")

class PasswordMismatchError(PaymentGatewayException):
    def __init__(self, detail: str = "Passwords do not match"):
        super().__init__(detail, "PASSWORD_MISMATCH")

class AuthenticationError(PaymentGatewayException):
    def __init__(self, detail: str = "Could not validate credentials"):
        super().__init__(detail, "AUTHENTICATION_FAILED")

class TokenExpiredError(AuthenticationError):
    def __init__(self):
        super().__init__("Access token has expired")

class InvalidResetTokenError(PaymentGatewayException):
    def __init__(self, detail: str = "Invalid or expired password reset token"):
        super().__init__(detail, "INVALID_RESET_TOKEN")

class PermissionDeniedError(PaymentGatewayException):
    def __init__(self, detail: str = "You do not have permission to perform this action"):
        super().__init__(detail, "PERMISSION_DENIED")

class APIKeyInvalidError(AuthenticationError):
    def __init__(self):
        super().__init__("Invalid API key provided")

class APIKeyRevokedError(AuthenticationError):
    def __init__(self):
        super().__init__("API key has been revoked")

class RateLimitExceededError(PaymentGatewayException):
    def __init__(self, detail: str = "Too many requests"):
        super().__init__(detail, "RATE_LIMIT_EXCEEDED")

class WebhookSignatureError(AuthenticationError):
    def __init__(self):
        super().__init__("Webhook signature verification failed")

class MerchantAccountNotFoundError(ResourceNotFoundError):
    def __init__(self, reason: str = ""):
        detail = f"Merchant account not found: {reason}" if reason else "Merchant account not found"
        super().__init__(detail)

class MerchantCreationError(PaymentGatewayException):
    def __init__(self, reason: str = ""):
        detail = f"Merchant creation failed: {reason}" if reason else "Merchant creation failed"
        super().__init__(detail, "MERCHANT_CREATION_FAILED")

class UserAlreadyVerifiedError(PaymentGatewayException):
    def __init__(self):
        super().__init__("User is already verified", "USER_ALREADY_VERIFIED")

class VerificationError(PaymentGatewayException):
    def __init__(self, reason: str = ""):
        detail = f"Failed to verify user: {reason}" if reason else "Failed to verify user"
        super().__init__(detail, "VERIFICATION_FAILED")

class KYCRequiredError(PermissionDeniedError):
    def __init__(self, detail: str = "KYC verification is required to perform this action"):
        super().__init__(detail)

class KYCPendingError(PermissionDeniedError):
    def __init__(self, detail: str = "KYC verification is still pending"):
        super().__init__(detail)

class ChargeNotFoundError(ResourceNotFoundError):
    def __init__(self):
        super().__init__("Charge")

class ChargeCreationError(PaymentGatewayException):
    def __init__(self, reason: str = ""):
        detail = f"Charge creation failed: {reason}" if reason else "Charge creation failed"
        super().__init__(detail, "CHARGE_CREATION_FAILED")

class PaymentFailedError(PaymentGatewayException):
    def __init__(self, reason: str = "The payment was declined"):
        super().__init__(reason, "PAYMENT_DECLINED")

class InvalidChargeAmountError(InvalidRequestError):
    def __init__(self, detail: str = "Charge amount must be a positive value"):
        super().__init__(detail)

class DuplicateChargeError(PaymentGatewayException):
    def __init__(self, detail: str = "A charge with this idempotency key already exists"):
        super().__init__(detail, "DUPLICATE_CHARGE")

class InsufficientFundsError(PaymentFailedError):
    def __init__(self):
        super().__init__("Insufficient funds for this operation")


def exception_to_http_response(exc: PaymentGatewayException, status_code: int = status.HTTP_400_BAD_REQUEST):
    """Converts a custom exception into a standardized HTTPException."""
    return HTTPException(
        status_code=status_code,
        detail={"error": exc.code, "message": exc.detail}
    )

class ExpiredResetTokenError(PaymentGatewayException):
    def __init__(self, detail: str = "Password reset token has expired"):
        super().__init__(detail, "RESET_TOKEN_EXPIRED")

class InvalidVerificationTokenError(PaymentGatewayException):
    def __init__(self, detail: str = "Invalid or expired email verification token"):
        super().__init__(detail, "INVALID_VERIFICATION_TOKEN")

class ExpiredVerificationTokenError(PaymentGatewayException):
    def __init__(self, detail: str = "Email verification token has expired"):
        super().__init__(detail, "VERIFICATION_TOKEN_EXPIRED")


class PayoutError:
    pass