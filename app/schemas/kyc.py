from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from datetime import datetime
from typing import Optional, Literal, List


class KYCDocumentUpload(BaseModel):
    document_type: Literal[
        'business_registration',
        'tax_certificate',
        'identity_proof',
        'address_proof',
        'bank_statement',
        'utility_bill',
        'other'
    ]
    file_name: str
    description: Optional[str] = None


class KYCDocumentRes(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    document_type: str
    file_url: str
    file_name: str
    description: Optional[str]
    status: str
    rejection_reason: Optional[str]
    uploaded_at: datetime
    reviewed_at: Optional[datetime]


class KYCVerificationRequest(BaseModel):
    document_ids: List[int] = Field(..., description="List of uploaded document IDs")
    additional_info: Optional[dict] = Field(default=None, description="Additional verification information")


class KYCVerificationRes(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    user_id: int
    kyc_status: str
    submitted_at: Optional[datetime]
    verified_at: Optional[datetime]
    rejection_reason: Optional[str]
    required_actions: Optional[List[str]] = Field(default=None)


class IdentityVerification(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    first_name: str
    last_name: str
    date_of_birth: datetime
    id_number: str
    id_type: str
    id_country: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state_province: str
    postal_code: str
    country: str

class IdentityVerificationCreate(IdentityVerification):
    pass

class IdentityVerificationRes(IdentityVerification):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class BusinessVerification(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    legal_business_name: str
    trading_name: Optional[str] = None
    business_registration_number: str
    tax_id: str
    business_type: str
    incorporation_date: datetime
    incorporation_country: str
    business_address_line1: str
    business_address_line2: Optional[str] = None
    business_city: str
    business_state_province: str
    business_postal_code: str
    business_country: str
    website: Optional[HttpUrl] = None
    business_description: str

class BusinessVerificationCreate(BusinessVerification):
    pass

class BusinessVerificationRes(BusinessVerification):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime


class RiskAssessment(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    risk_level: Literal['low', 'medium', 'high']
    risk_factors: List[str]
    review_required: bool = Field(default=False)
    notes: Optional[str] = None

class RiskAssessmentRes(RiskAssessment):
    model_config = ConfigDict(from_attributes=True)
    merchant_id: str
    assessed_at: datetime
    assessed_by: Optional[str] = Field(None)