"""
Payment Gateway Schemas Package.
Export all schemas for easy importing.
"""


from .account import (
    User,
    UserCreate,
    UserVer,
    UserVerRes,
    UserVerifiedInfoRes,
    UserRes,
    UserDetailsRes,
    UserUpdate,
    UserUpdateRes,
    UserUpdateVer,
    UserUpdateVerRes
)

from .token import Token, TokenData

# Merchant schemas
from .merchant import (
    MerchantAccountCreate,
    MerchantAccountRes,
    MerchantBalanceRes,
    MerchantStatusUpdate,
    TransactionLimits,
    TransactionLimitsRes,
    FeeStructure,
    FeeStructureRes,
    MerchantSettings,
    MerchantSettingsRes,
    MerchantMetadata
)


from .api_key import (
    APIKeyCreate,
    APIKeyRes,
    APIKeyFullRes,
    APIKeyRevoke,
    WebhookEndpointCreate,
    WebhookEndpointRes,
    WebhookEndpointUpdate,
    WebhookDelivery,
    WebhookDeliveryRes,
    APIVersionInfo
)


from .kyc import (
    KYCDocumentUpload,
    KYCDocumentRes,
    KYCVerificationRequest,
    KYCVerificationRes,
    IdentityVerification,
    BusinessVerification,
    RiskAssessment,
    RiskAssessmentRes
)

from .payout import (
    PayoutAccountCreate,
    PayoutAccountRes,
    PayoutAccountVerification,
    PayoutCreate,
    PayoutRes,
    SettlementScheduleUpdate,
    SettlementScheduleRes,
    SettlementReport,
    SettlementReportRes
)

__all__ = [
    # User
    "User",
    "UserCreate",
    "UserVer",
    "UserVerRes",
    "UserVerifiedInfoRes",
    "UserRes",
    "UserDetailsRes",
    "UserUpdate",
    "UserUpdateRes",
    "UserUpdateVer",
    "UserUpdateVerRes",
    # Token
    "Token",
    "TokenData",
    # Merchant
    "MerchantAccountCreate",
    "MerchantAccountRes",
    "MerchantBalanceRes",
    "MerchantStatusUpdate",
    "TransactionLimits",
    "TransactionLimitsRes",
    "FeeStructure",
    "FeeStructureRes",
    "MerchantSettings",
    "MerchantSettingsRes",
    "MerchantMetadata",
    # API Key
    "APIKeyCreate",
    "APIKeyRes",
    "APIKeyFullRes",
    "APIKeyRevoke",
    "WebhookEndpointCreate",
    "WebhookEndpointRes",
    "WebhookEndpointUpdate",
    "WebhookDelivery",
    "WebhookDeliveryRes",
    "APIVersionInfo",
    # KYC
    "KYCDocumentUpload",
    "KYCDocumentRes",
    "KYCVerificationRequest",
    "KYCVerificationRes",
    "IdentityVerification",
    "BusinessVerification",
    "RiskAssessment",
    "RiskAssessmentRes",
    # Payout
    "PayoutAccountCreate",
    "PayoutAccountRes",
    "PayoutAccountVerification",
    "PayoutCreate",
    "PayoutRes",
    "SettlementScheduleUpdate",
    "SettlementScheduleRes",
    "SettlementReport",
    "SettlementReportRes",
]

