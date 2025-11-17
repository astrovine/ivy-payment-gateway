import uuid
import enum

from sqlalchemy.orm import relationship, foreign
from ..utilities.db_con import Base
from sqlalchemy import (
    ForeignKey,
    Integer,
    String,
    Column,
    Boolean,
    TIMESTAMP,
    Numeric,
    UniqueConstraint,
    Enum as SAEnum,
    DateTime,
)
from sqlalchemy.sql import func


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


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    country = Column(String, nullable=False)
    password_reset_token = Column(String, nullable=True)
    password_reset_expires = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superadmin = Column(Boolean, default=False, nullable=False)
    charges = relationship("Charge", back_populates="user")
    verified_info = relationship("UserVerified", back_populates="user", uselist=False)
    merchant_info = relationship("MerchantAccount", back_populates="user_info", uselist=False)


class UserVerified(Base):
    __tablename__ = "user_verified"
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    industry = Column(String, nullable=False)
    staff_size = Column(Integer, nullable=False)
    business_name = Column(String, nullable=False)
    business_type = Column(SAEnum(BusinessType, name="business_type_enum"), nullable=False)
    business_email = Column(String, nullable=True, unique=True)
    business_website = Column(String, nullable=True)
    business_description = Column(String, nullable=True)
    location = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    support_email = Column(String, nullable=True)
    support_phone = Column(String, nullable=True)
    bank_account_name = Column(String, nullable=False)
    bank_account_number = Column(String, nullable=False)
    bank_name = Column(String, nullable=True)
    bank_code = Column(String, nullable=True)
    tax_id = Column(String, nullable=True)
    user = relationship("User", back_populates="verified_info")


class Charge(Base):
    __tablename__ = "charges"
    id = Column(String, primary_key=True, default=lambda: f"ch_{uuid.uuid4().hex}")
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    description = Column(String, nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="NGN", nullable=False)
    status = Column(String, default="pending", nullable=False)
    idempotency_key = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    user = relationship("User", back_populates="charges")
    __table_args__ = (
        UniqueConstraint('user_id', 'idempotency_key', name='_user_idempotency_uc'),)


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    refresh_token = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    revoked = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)


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


class MerchantAccount(Base):
    __tablename__ = "merchant_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    merchant_id = Column(String, nullable=False, unique=True)

    account_status = Column(SAEnum(AccountStatus, name="account_status_enum"), nullable=False,
                            default=AccountStatus.active)
    verification_status = Column(SAEnum(VerificationStatus, name="verification_status_enum"), nullable=False,
                                 default=VerificationStatus.unverified)
    kyc_status = Column(SAEnum(KYCStatus, name="kyc_status_enum"), nullable=False, default=KYCStatus.not_started)
    kyc_verified_at = Column(TIMESTAMP(timezone=True), nullable=True)

    currency = Column(String(3), nullable=False, default="NGN")
    available_balance = Column(Numeric(19, 4), nullable=False, default=0.0000)
    pending_balance = Column(Numeric(19, 4), nullable=False, default=0.0000)
    reserved_balance = Column(Numeric(19, 4), nullable=False, default=0.0000)
    settlement_schedule = Column(String, nullable=False, default="daily")
    settlement_delay_days = Column(Integer, nullable=False, default=2)
    minimum_payout_amount = Column(Numeric(19, 4), nullable=True)
    next_settlement_date = Column(TIMESTAMP(timezone=True), nullable=True)
    risk_level = Column(SAEnum(RiskLevel, name="risk_level_enum"), nullable=False, default=RiskLevel.low)
    onboarding_completed = Column(Boolean, nullable=False, default=False)
    onboarding_completed_at = Column(TIMESTAMP(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    user_info = relationship("User", back_populates="merchant_info")

    kyc_info = relationship(
        "KYCVerification",
        primaryjoin=lambda: foreign(KYCVerification.user_id) == MerchantAccount.user_id,
        back_populates="merchant_info",
        uselist=False,
    )
    identity_info = relationship(
        "IdentityVerification",
        primaryjoin=lambda: foreign(IdentityVerification.user_id) == MerchantAccount.user_id,
        back_populates="merchant_info",
        uselist=False,
    )
    business_info = relationship(
        "BusinessVerification",
        primaryjoin=lambda: foreign(BusinessVerification.user_id) == MerchantAccount.user_id,
        back_populates="merchant_info",
        uselist=False,
    )

    payout_info = relationship("Payout", back_populates="merchant")


class TransactionLimit(Base):
    __tablename__ = "transaction_limits"

    id = Column(Integer, primary_key=True, autoincrement=True)
    merchant_id = Column(String, ForeignKey("merchant_accounts.merchant_id", ondelete="CASCADE"), nullable=False,
                         unique=True)

    daily_transaction_limit = Column(Numeric(19, 4), nullable=True)
    monthly_transaction_limit = Column(Numeric(19, 4), nullable=True)
    single_transaction_limit = Column(Numeric(19, 4), nullable=True)
    daily_transaction_count = Column(Integer, nullable=True)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class FeeStructure(Base):
    __tablename__ = "fee_structures"

    id = Column(Integer, primary_key=True, autoincrement=True)
    merchant_id = Column(String, ForeignKey("merchant_accounts.merchant_id", ondelete="CASCADE"), nullable=False,
                         unique=True)
    percentage_fee = Column(Numeric(5, 4), nullable=False, default=0.0290)
    fixed_fee = Column(Numeric(10, 4), nullable=False, default=0.3000)
    chargeback_fee = Column(Numeric(10, 4), nullable=False, default=15.0000)
    refund_fee = Column(Numeric(10, 4), nullable=False, default=0.0000)
    currency = Column(String(3), nullable=False, default="USD")

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    merchant_id = Column(String, ForeignKey("merchant_accounts.merchant_id", ondelete="CASCADE"), nullable=False)

    name = Column(String, nullable=False)
    api_key = Column(String, nullable=False, unique=True)
    key_prefix = Column(String, nullable=False)
    key_type = Column(String, nullable=False)
    environment = Column(String, nullable=False, default="test")

    is_active = Column(Boolean, nullable=False, default=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revoked_at = Column(TIMESTAMP(timezone=True), nullable=True)
    revoke_reason = Column(String, nullable=True)


class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"

    id = Column(Integer, primary_key=True, autoincrement=True)
    merchant_id = Column(String, ForeignKey("merchant_accounts.merchant_id", ondelete="CASCADE"), nullable=False)

    url = Column(String, nullable=False)
    description = Column(String, nullable=True)
    events = Column(String, nullable=False)
    secret = Column(String, nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    api_version = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class KYCDocument(Base):
    __tablename__ = "kyc_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    document_type = Column(String, nullable=False)
    file_url = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    status = Column(String, nullable=False, default="pending")
    rejection_reason = Column(String, nullable=True)

    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reviewed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    reviewed_by = Column(String, nullable=True)


class KYCVerification(Base):
    __tablename__ = "kyc_verifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)

    kyc_status = Column(SAEnum(KYCStatus, name="kyc_verification_status_enum"), nullable=False,
                        default=KYCStatus.not_started)
    submitted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    verified_at = Column(TIMESTAMP(timezone=True), nullable=True)
    rejection_reason = Column(String, nullable=True)
    required_actions = Column(String, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    merchant_info = relationship(
        "MerchantAccount",
        primaryjoin=lambda: foreign(KYCVerification.user_id) == MerchantAccount.user_id,
        back_populates="kyc_info",
        uselist=False,
    )


class IdentityVerification(Base):
    __tablename__ = "identity_verifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)

    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(DateTime(timezone=True), nullable=False)
    id_number = Column(String, nullable=False)
    id_type = Column(String, nullable=False)
    id_country = Column(String, nullable=False)
    address_line1 = Column(String, nullable=False)
    address_line2 = Column(String, nullable=True)
    city = Column(String, nullable=False)
    state_province = Column(String, nullable=False)
    postal_code = Column(String, nullable=False)
    country = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    merchant_info = relationship(
        "MerchantAccount",
        primaryjoin=lambda: foreign(IdentityVerification.user_id) == MerchantAccount.user_id,
        back_populates="identity_info",
        uselist=False,
    )


class BusinessVerification(Base):
    __tablename__ = "business_verifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)

    legal_business_name = Column(String, nullable=False)
    trading_name = Column(String, nullable=True)
    business_registration_number = Column(String, nullable=False)
    tax_id = Column(String, nullable=False)
    business_type = Column(String, nullable=False)
    incorporation_date = Column(DateTime(timezone=True), nullable=False)
    incorporation_country = Column(String, nullable=False)
    business_address_line1 = Column(String, nullable=False)
    business_address_line2 = Column(String, nullable=True)
    business_city = Column(String, nullable=False)
    business_state_province = Column(String, nullable=False)
    business_postal_code = Column(String, nullable=False)
    business_country = Column(String, nullable=False)
    website = Column(String, nullable=True)
    business_description = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    merchant_info = relationship(
        "MerchantAccount",
        primaryjoin=lambda: foreign(BusinessVerification.user_id) == MerchantAccount.user_id,
        back_populates="business_info",
        uselist=False,
    )


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    merchant_id = Column(String, ForeignKey("merchant_accounts.merchant_id", ondelete="CASCADE"), nullable=False)

    risk_level = Column(SAEnum(RiskLevel, name="risk_assessment_level_enum"), nullable=False)
    risk_factors = Column(String, nullable=True)
    review_required = Column(Boolean, nullable=False, default=False)
    notes = Column(String, nullable=True)
    assessed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    assessed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class PayoutAccount(Base):
    __tablename__ = "payout_accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    merchant_id = Column(String, ForeignKey("merchant_accounts.merchant_id", ondelete="CASCADE"), nullable=False)

    account_holder_name = Column(String, nullable=False)
    account_number = Column(String, nullable=False)
    account_number_last4 = Column(String, nullable=False)
    routing_number = Column(String, nullable=False)
    bank_name = Column(String, nullable=False)
    bank_country = Column(String, nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    account_type = Column(String, nullable=False, default="business")

    is_primary = Column(Boolean, nullable=False, default=False)
    is_verified = Column(Boolean, nullable=False, default=False)
    verification_status = Column(String, nullable=False, default="pending")

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    verified_at = Column(DateTime(timezone=True), nullable=True)


class PayoutStatus(enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Payout(Base):
    __tablename__ = "payouts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    merchant_id = Column(String, ForeignKey("merchant_accounts.merchant_id"), nullable=False)
    payout_account_id = Column(Integer, ForeignKey("payout_accounts.id", ondelete="RESTRICT"), nullable=False)
    amount = Column(Numeric(19, 4), nullable=False)
    currency = Column(String(3), nullable=False, default="NGN")
    status = Column(SAEnum(PayoutStatus, name="payout_status_enum"),
                    nullable=False, default=PayoutStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    merchant = relationship("MerchantAccount", back_populates="payout_info")
    failure_reason = Column(String, nullable=True)


class AuditLog(Base):
    """Audit trail for security-critical operations"""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    merchant_id = Column(String, nullable=True)

    action = Column(String, nullable=False)
    resource_type = Column(String, nullable=False)
    resource_id = Column(String, nullable=True)

    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    changes = Column(String, nullable=True)
    extra_data = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class LedgerTransaction(Base):
    __tablename__ = "ledger_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)

    charge_id = Column(String, ForeignKey("charges.id"), nullable=True, index=True)

    payout_id = Column(Integer, ForeignKey("payouts.id"), nullable=True, index=True)
    # refund_id = Column(String, ForeignKey("refunds.id"), nullable=True, index=True)

    merchant_id = Column(String, ForeignKey("merchant_accounts.merchant_id"), nullable=False, index=True)

    transaction_type = Column(SAEnum(TransactionType, name="transaction_type_enum"), nullable=False)
    amount = Column(Numeric(19, 4), nullable=False)
    currency = Column(String(3), nullable=False)
    debit_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    credit_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    description = Column(String, nullable=True)


class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    merchant_id = Column(String, ForeignKey("merchant_accounts.merchant_id"), nullable=True, index=True)

    account_type = Column(SAEnum(AccountType, name="account_type_enum"), nullable=False)
    currency = Column(String(3), nullable=False, default="NGN")
    balance = Column(Numeric(19, 4), nullable=False, default=0.0000)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint('merchant_id', 'account_type', 'currency', name='_merchant_account_type_currency_uc'),
    )


class MerchantSettings(Base):
    __tablename__ = "merchant_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    merchant_id = Column(String, ForeignKey("merchant_accounts.merchant_id", ondelete="CASCADE"), nullable=False,
                         unique=True)

    email_notifications = Column(Boolean, nullable=False, default=True)
    sms_notifications = Column(Boolean, nullable=False, default=False)
    webhook_notifications = Column(Boolean, nullable=False, default=True)
    two_factor_enabled = Column(Boolean, nullable=False, default=False)
    notification_email = Column(String, nullable=True)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    webhook_id = Column(Integer, ForeignKey("webhook_endpoints.id", ondelete="CASCADE"), nullable=False, index=True)
    event = Column(String, nullable=False)
    payload = Column(String, nullable=True)
    status = Column(String, nullable=False, default="pending")
    http_status = Column(Integer, nullable=True)
    response_body = Column(String, nullable=True)
    attempts = Column(Integer, nullable=False, default=0)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    merchant_id = Column(String, ForeignKey("merchant_accounts.merchant_id", ondelete="CASCADE"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    type = Column(String, nullable=False)
    message = Column(String, nullable=False)
    data = Column(String, nullable=True)
    is_read = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
