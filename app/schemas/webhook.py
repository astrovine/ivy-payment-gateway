from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, List, Any
from datetime import datetime

class WebhookCreate(BaseModel):
    url: HttpUrl
    description: Optional[str]
    events: List[str]
    secret: Optional[str]
    enabled: Optional[bool] = True
    api_version: Optional[str]

class WebhookUpdate(BaseModel):
    url: Optional[HttpUrl]
    description: Optional[str]
    events: Optional[List[str]]
    secret: Optional[str]
    enabled: Optional[bool]
    api_version: Optional[str]

class WebhookRes(BaseModel):
    id: int
    merchant_id: Optional[str]
    url: HttpUrl
    description: Optional[str]
    events: List[str]
    secret: Optional[str]
    enabled: bool
    api_version: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True

class WebhookDeliveryRes(BaseModel):
    id: int
    webhook_id: int
    event: str
    payload: Any
    status: str
    http_status: Optional[int]
    response_body: Optional[str]
    attempts: int
    last_attempt_at: Optional[datetime]
    created_at: datetime

    class Config:
        orm_mode = True

