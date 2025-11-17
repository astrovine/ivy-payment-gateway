
from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from decimal import Decimal

class ChargeCreate(BaseModel):
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    currency: str = Field(..., min_length=3, max_length=3)
    description: str = Field(..., min_length=1)
    idempotency_key: str | None = None
    payment_token: str | None = None

class ChargeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    user_id: int
    amount: Decimal
    currency: str
    status: str
    description: str
    created_at: datetime
