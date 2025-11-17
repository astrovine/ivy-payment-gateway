from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from pydantic import EmailStr

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    id: Optional[str] = None

class TokenData(BaseModel):
    id: str | None = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class LoginUser(BaseModel):
    id: int
    email: EmailStr
    name: str
    country: Optional[str] = None
    created_at: Optional[datetime] = None
    # New flags for frontend gating
    is_verified: bool
    has_merchant_account: bool
    onboarding_stage: str  # e.g. account_created | verified | merchant_created | active

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str
    user: LoginUser
