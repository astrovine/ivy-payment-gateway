"""
Merchant account schemas for payment gateway operations.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Literal, Dict, Any
from decimal import Decimal


class MerchantAccountCreate(BaseModel):
    """Schema for creating a merchant account after user verification."""
    currency: str = Field(default="NGN", description="Default transaction currency")
    settlement_schedule: Literal['daily', 'weekly', 'monthly'] = Field(default='daily')

class MerchantRes(MerchantAccountCreate):
    model_config = ConfigDict(from_attributes=True)

class MerchantAccountRes(BaseModel):
    """Response schema for merchant account."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    merchant_id: str
    account_status: str
    verification_status: str
    kyc_status: str
    currency: str
    # available_balance: Decimal
    # pending_balance: Decimal
    # reserved_balance: Decimal
    settlement_schedule: str
    risk_level: str
    created_at: datetime
    updated_at: Optional[datetime]

class MerchantAccountUpdate(BaseModel):
    """Schema for partially updating a merchant account."""
    currency: Optional[str] = Field(None, min_length=3, max_length=3)
    settlement_schedule: Optional[Literal['daily', 'weekly', 'monthly']] = Field(None)

class MerchantBalanceRes(BaseModel):
    """Schema for merchant balance information."""
    model_config = ConfigDict(from_attributes=True)

    available_balance: Decimal
    pending_balance: Decimal
    reserved_balance: Decimal
    currency: str


class MerchantStatusUpdate(BaseModel):
    """Schema for updating merchant account status."""
    account_status: Optional[Literal['active', 'suspended', 'restricted', 'closed']] = None
    verification_status: Optional[Literal['unverified', 'pending', 'verified', 'rejected']] = None
    kyc_status: Optional[Literal['not_started', 'pending', 'verified', 'failed']] = None
    risk_level: Optional[Literal['low', 'medium', 'high']] = None


class TransactionLimits(BaseModel):
    """Schema for merchant transaction limits."""
    model_config = ConfigDict(from_attributes=True)

    daily_transaction_limit: Optional[Decimal] = Field(default=None, description="Daily transaction limit")
    monthly_transaction_limit: Optional[Decimal] = Field(default=None, description="Monthly transaction limit")
    single_transaction_limit: Optional[Decimal] = Field(default=None, description="Single transaction limit")
    daily_transaction_count: Optional[int] = Field(default=None, description="Max transactions per day")


class TransactionLimitsRes(TransactionLimits):
    """Response schema for transaction limits."""
    model_config = ConfigDict(from_attributes=True)

    merchant_id: str
    updated_at: datetime


class FeeStructure(BaseModel):
    """Schema for merchant fee structure."""
    model_config = ConfigDict(from_attributes=True)

    percentage_fee: Decimal = Field(default=Decimal("2.9"), description="Percentage fee per transaction")
    fixed_fee: Decimal = Field(default=Decimal("0.30"), description="Fixed fee per transaction")
    chargeback_fee: Decimal = Field(default=Decimal("15.00"), description="Fee for chargebacks")
    refund_fee: Decimal = Field(default=Decimal("0.00"), description="Fee for refunds")


class FeeStructureRes(FeeStructure):
    """Response schema for fee structure."""
    model_config = ConfigDict(from_attributes=True)

    merchant_id: str
    updated_at: datetime


class MerchantSettings(BaseModel):
    """Schema for merchant account settings."""
    model_config = ConfigDict(from_attributes=True)

    email_notifications: bool = Field(default=True)
    sms_notifications: bool = Field(default=False)
    webhook_notifications: bool = Field(default=True)
    two_factor_enabled: bool = Field(default=False)
    ip_whitelist: Optional[list[str]] = Field(default=None)
    notification_email: Optional[str] = None


class MerchantSettingsRes(MerchantSettings):
    """Response schema for merchant settings."""
    model_config = ConfigDict(from_attributes=True)

    merchant_id: str
    updated_at: datetime


class MerchantMetadata(BaseModel):
    """Schema for custom merchant metadata."""
    model_config = ConfigDict(from_attributes=True)

    metadata: Dict[str, Any] = Field(default_factory=dict, description="Custom merchant metadata")

