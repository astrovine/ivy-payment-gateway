from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class UserSimple(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    name: str
    country: str
    is_superadmin: bool


class MerchantAccountAdmin(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    id: int
    merchant_id: str
    account_status: str
    verification_status: str
    kyc_status: str
    kyc_verified_at: Optional[datetime] = None
    currency: str
    available_balance: float
    pending_balance: float
    reserved_balance: float
    risk_level: str
    created_at: datetime
    updated_at: datetime
    user_info: Optional[UserSimple] = None


class MerchantsListResponse(BaseModel):
    total: int
    merchants: List[MerchantAccountAdmin]


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int]
    merchant_id: Optional[str]
    action: str
    resource_type: str
    resource_id: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    changes: Optional[str]
    extra_data: Optional[str]
    created_at: datetime


class AuditLogsListResponse(BaseModel):
    total: int
    logs: List[AuditLogResponse]


class ChargeAdmin(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: int
    description: str
    amount: float
    currency: str
    status: str
    created_at: datetime
    user: Optional[UserSimple] = None


class TransactionsListResponse(BaseModel):
    total: int
    transactions: List[ChargeAdmin]


class UserVerifiedInfoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='ignore')

    id: int
    user_id: int
    business_name: Optional[str] = None
    industry: Optional[str] = None
    staff_size: Optional[str] = None
    location: Optional[str] = None
    business_website: Optional[str] = None


class KYCDocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='ignore')

    id: int
    user_id: int
    document_type: Optional[str] = None
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    uploaded_at: Optional[datetime] = None


class KYCVerificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='ignore')

    id: int
    user_id: int
    kyc_status: Optional[str] = None
    submitted_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None


class IdentityVerificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='ignore')

    id: int
    user_id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    id_number: Optional[str] = None
    id_type: Optional[str] = None
    country: Optional[str] = None


class BusinessVerificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra='ignore')

    id: int
    user_id: int
    legal_business_name: Optional[str] = None
    business_registration_number: Optional[str] = None
    tax_id: Optional[str] = None
    business_type: Optional[str] = None


class MerchantDetailsResponse(BaseModel):
    model_config = ConfigDict(extra='ignore')

    merchant: MerchantAccountAdmin
    user: UserSimple
    verified_info: Optional[UserVerifiedInfoResponse] = None
    kyc_status: Optional[KYCVerificationResponse] = None
    kyc_documents: Optional[List[KYCDocumentResponse]] = []
    identity_verification: Optional[IdentityVerificationResponse] = None
    business_verification: Optional[BusinessVerificationResponse] = None


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    merchant_id: Optional[str] = None
    user_id: Optional[int] = None
    type: str
    message: str
    data: Optional[str] = None
    is_read: bool
    created_at: datetime
    updated_at: datetime
