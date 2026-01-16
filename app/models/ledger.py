from .base import (
    Base, Column, Integer, String, DateTime, ForeignKey, SAEnum, Numeric, UniqueConstraint, func
)
from .enums import TransactionType, AccountType


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


class LedgerTransaction(Base):
    __tablename__ = "ledger_transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)

    charge_id = Column(String, ForeignKey("charges.id"), nullable=True, index=True)

    payout_id = Column(Integer, ForeignKey("payouts.id"), nullable=True, index=True)

    merchant_id = Column(String, ForeignKey("merchant_accounts.merchant_id"), nullable=False, index=True)

    transaction_type = Column(SAEnum(TransactionType, name="transaction_type_enum"), nullable=False)
    amount = Column(Numeric(19, 4), nullable=False)
    currency = Column(String(3), nullable=False)
    debit_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    credit_account_id = Column(Integer, ForeignKey("accounts.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    description = Column(String, nullable=True)
