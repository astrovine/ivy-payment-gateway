from .base import Base

from .enums import (
    BusinessType, TransactionType, AccountType, AccountStatus, 
    VerificationStatus, KYCStatus, RiskLevel, PayoutStatus
)

from .user import User, UserVerified, RefreshToken
from .merchant import MerchantAccount, TransactionLimit, FeeStructure, MerchantSettings
from .payment import Charge, PayoutAccount, Payout
from .ledger import Account, LedgerTransaction
from .kyc import KYCDocument, KYCVerification, IdentityVerification, BusinessVerification, RiskAssessment
from .webhook import WebhookEndpoint, WebhookDelivery
from .api_key import APIKey
from .audit import AuditLog
from .notification import Notification


class _DbModelsCompat:
    Base = Base
    
    BusinessType = BusinessType
    TransactionType = TransactionType
    AccountType = AccountType
    AccountStatus = AccountStatus
    VerificationStatus = VerificationStatus
    KYCStatus = KYCStatus
    RiskLevel = RiskLevel
    PayoutStatus = PayoutStatus
    
    User = User
    UserVerified = UserVerified
    RefreshToken = RefreshToken
    
    MerchantAccount = MerchantAccount
    TransactionLimit = TransactionLimit
    FeeStructure = FeeStructure
    MerchantSettings = MerchantSettings
    
    Charge = Charge
    PayoutAccount = PayoutAccount
    Payout = Payout
    
    Account = Account
    LedgerTransaction = LedgerTransaction
    
    KYCDocument = KYCDocument
    KYCVerification = KYCVerification
    IdentityVerification = IdentityVerification
    BusinessVerification = BusinessVerification
    RiskAssessment = RiskAssessment
    
    WebhookEndpoint = WebhookEndpoint
    WebhookDelivery = WebhookDelivery
    
    APIKey = APIKey
    AuditLog = AuditLog
    Notification = Notification


db_models = _DbModelsCompat()
