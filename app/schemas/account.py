from pydantic import BaseModel, EmailStr, HttpUrl, ConfigDict
from datetime import datetime
from typing import Literal, Optional


class User(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserCreate(User):
    country: str
    # terms_accepted: bool = Field(default=False, description="User must accept terms and conditions")

class UserVer(BaseModel):
    industry: str
    staff_size: int
    business_name: str
    business_type: Literal['Starter', 'Registered']
    business_email: Optional[str] = None
    business_website: Optional[HttpUrl] = None
    business_description: Optional[str] = None
    location: str
    phone_number: str
    support_email: Optional[EmailStr] = None
    support_phone: Optional[str] = None
    bank_account_name: str
    bank_account_number: str
    bank_name: Optional[str] = None
    bank_code: Optional[str] = None  # routing number or sort code
    tax_id: Optional[str] = None  # Business registration or tax ID

class UserVerRes(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)

    business_name: str
    industry: str
    staff_size: int

class UserVerifiedInfoRes(BaseModel):
    model_config = ConfigDict(from_attributes=True, use_enum_values=True)
    industry: str
    staff_size: int
    business_name: str
    business_type: str
    business_email: Optional[str] = None
    business_website: Optional[str] = None
    business_description: Optional[str] = None
    location: str
    phone_number: str
    support_email: Optional[str] = None
    support_phone: Optional[str] = None
    bank_account_name: str
    bank_account_number: str
    bank_name: Optional[str] = None
    bank_code: Optional[str] = None
    tax_id: Optional[str] = None
    verification_status: Optional[str] = None

class UserRes(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    created_at: datetime

class UserUpdatePassword(BaseModel):
    old_password: str
    password: str
    confirm_password: str


class UserDetailsRes(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    name: str
    email: EmailStr
    country: str
    verified_info: Optional[UserVerifiedInfoRes] = None

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    country: Optional[str] = None

class UserUpdateRes(UserUpdate):
    model_config = ConfigDict(from_attributes=True)

class UserUpdateVer(BaseModel):
    industry: Optional[str] = None
    staff_size: Optional[int] = None
    business_name: Optional[str] = None
    business_type: Optional[Literal['Starter', 'Registered']] = None
    business_email: Optional[str] = None
    business_website: Optional[HttpUrl] = None
    business_description: Optional[str] = None
    location: Optional[str] = None
    phone_number: Optional[str] = None
    support_email: Optional[EmailStr] = None
    support_phone: Optional[str] = None
    bank_account_name: Optional[str] = None
    bank_account_number: Optional[str] = None
    bank_name: Optional[str] = None
    bank_code: Optional[str] = None
    tax_id: Optional[str] = None

class UserUpdateVerRes(UserUpdateVer):
    model_config = ConfigDict(from_attributes=True)

class UserMeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr
    name: str
    country: Optional[str] = None
    created_at: Optional[datetime] = None
    is_verified: bool
    has_merchant_account: bool
    onboarding_stage: str
    is_superadmin: bool
