import uuid
from .base import (
    Base, relationship, Column, Integer, String, Boolean,
    DateTime, ForeignKey, SAEnum, Numeric, UniqueConstraint, func, TIMESTAMP
)
from .enums import PayoutStatus


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
