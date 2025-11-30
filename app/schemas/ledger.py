from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional


class BalanceHistory(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    charge_id: Optional[str] = None
    transaction_type: str
    amount: float
    currency: str
    created_at: datetime
