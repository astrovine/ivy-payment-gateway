"""
Payout and settlement schemas for payment gateway.
"""
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Literal
from decimal import Decimal


class PayoutAccountCreate(BaseModel):
    """Schema for creating/adding a payout account."""
    account_holder_name: str
    account_number: str = Field(..., description="Bank account number")
    routing_number: str = Field(..., description="Bank routing number / sort code")
    bank_name: str
    bank_country: str = Field(..., description="Bank country (ISO code)")
    currency: str = Field(default="USD", description="Account currency")
    account_type: Literal['checking', 'savings', 'business'] = Field(default='business')
    is_primary: bool = Field(default=False, description="Set as primary payout account")


class PayoutAccountRes(BaseModel):
    """Response schema for payout account."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    merchant_id: str
    account_holder_name: str
    account_number_last4: str  # Only last 4 digits
    routing_number: str
    bank_name: str
    bank_country: str
    currency: str
    account_type: str
    is_primary: bool
    is_verified: bool
    verification_status: Literal['pending', 'verified', 'failed']
    created_at: datetime
    verified_at: Optional[datetime]

class PayoutAccountUpdate(BaseModel):
    """Schema for updating a payout account."""
    account_holder_name: Optional[str] = None
    is_primary: Optional[bool] = None


class PayoutAccountVerification(BaseModel):
    """Schema for verifying payout account (micro-deposits)."""
    deposit_amount_1: Decimal = Field(..., description="First micro-deposit amount")
    deposit_amount_2: Decimal = Field(..., description="Second micro-deposit amount")


class PayoutCreate(BaseModel):
    """Schema for creating a payout/settlement."""
    payout_account_id: int
    amount: Decimal = Field(..., gt=0, description="Payout amount")
    currency: str = Field(default="USD")
    description: Optional[str] = None
    metadata: Optional[dict] = Field(default=None, description="Custom metadata")


class PayoutRes(BaseModel):
    """Response schema for payout."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    merchant_id: str
    payout_account_id: int
    amount: Decimal
    currency: str
    status: str
    failure_reason: Optional[str] = None
    processed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None



class SettlementScheduleUpdate(BaseModel):
    """Schema for updating settlement schedule."""
    schedule: Literal['daily', 'weekly', 'bi_weekly', 'monthly'] = Field(..., description="Settlement frequency")
    delay_days: int = Field(default=2, ge=0, le=30, description="Days to delay settlement")
    minimum_payout_amount: Optional[Decimal] = Field(default=None, description="Minimum amount for payout")


class SettlementScheduleRes(SettlementScheduleUpdate):
    """Response schema for settlement schedule."""
    model_config = ConfigDict(from_attributes=True)

    merchant_id: str
    next_settlement_date: Optional[datetime]
    updated_at: datetime



class SettlementReport(BaseModel):
    """Schema for settlement report."""
    model_config = ConfigDict(from_attributes=True)

    merchant_id: str
    settlement_period_start: datetime
    settlement_period_end: datetime
    total_transactions: int
    total_amount: Decimal
    total_fees: Decimal
    total_refunds: Decimal
    total_chargebacks: Decimal
    net_settlement: Decimal
    currency: str
    status: Literal['pending', 'processing', 'completed', 'failed']



class SettlementReportRes(SettlementReport):
    """Response schema for settlement report."""
    model_config = ConfigDict(from_attributes=True)
    id: int
    payout_id: Optional[int]
    created_at: datetime
    completed_at: Optional[datetime]
