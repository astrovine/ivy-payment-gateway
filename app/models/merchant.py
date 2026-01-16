from .base import (
    Base, relationship, foreign, Column, Integer, String, Boolean, TIMESTAMP,
    DateTime, ForeignKey, SAEnum, Numeric, func
)
from .enums import AccountStatus, VerificationStatus, KYCStatus, RiskLevel


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
        primaryjoin="foreign(KYCVerification.user_id) == MerchantAccount.user_id",
        back_populates="merchant_info",
        uselist=False,
    )
    identity_info = relationship(
        "IdentityVerification",
        primaryjoin="foreign(IdentityVerification.user_id) == MerchantAccount.user_id",
        back_populates="merchant_info",
        uselist=False,
    )
    business_info = relationship(
        "BusinessVerification",
        primaryjoin="foreign(BusinessVerification.user_id) == MerchantAccount.user_id",
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
    fixed_fee = Column(Numeric( 10, 4), nullable=False, default=0.3000)
    chargeback_fee = Column(Numeric(10, 4), nullable=False, default=15.0000)
    refund_fee = Column(Numeric(10, 4), nullable=False, default=0.0000)
    currency = Column(String(3), nullable=False, default="USD")

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class MerchantSettings(Base):
    __tablename__ = "merchant_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    merchant_id = Column(String, ForeignKey("merchant_accounts.merchant_id", ondelete="CASCADE"), nullable=False,
                         unique=True)

    email_notifications = Column(Boolean, nullable=False, default=True)
    sms_notifications = Column(Boolean, nullable=False, default=False)
    webhook_notifications = Column(Boolean, nullable=False, default=True)
    two_factor_enabled = Column(Boolean, nullable=False, default=False)
    two_factor_secret = Column(String, nullable=True)  # Encrypted TOTP secret
    notification_email = Column(String, nullable=True)

    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
