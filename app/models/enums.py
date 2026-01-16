import enum


class BusinessType(enum.Enum):
    Starter = "Starter"
    Registered = "Registered"


class TransactionType(enum.Enum):
    CHARGE = "CHARGE"
    REFUND = "REFUND"
    PAYOUT = "PAYOUT"
    FEE = "FEE"


class AccountType(enum.Enum):
    MERCHANT_PENDING = "MERCHANT_PENDING"
    MERCHANT_AVAILABLE = "MERCHANT_AVAILABLE"
    PLATFORM_REVENUE = "PLATFORM_REVENUE"
    PLATFORM_PAYABLE = "PLATFORM_PAYABLE"
    SYSTEM_HOLDING = "SYSTEM_HOLDING"


class AccountStatus(enum.Enum):
    active = "active"
    suspended = "suspended"
    restricted = "restricted"
    closed = "closed"


class VerificationStatus(enum.Enum):
    unverified = "unverified"
    pending = "pending"
    verified = "verified"
    rejected = "rejected"


class KYCStatus(enum.Enum):
    not_started = "not_started"
    pending = "pending"
    verified = "verified"
    failed = "failed"


class RiskLevel(enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class PayoutStatus(enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
