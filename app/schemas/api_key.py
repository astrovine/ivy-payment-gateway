from pydantic import BaseModel, Field, HttpUrl, ConfigDict
from datetime import datetime
from typing import Optional, Literal, List


class APIKeyCreate(BaseModel):
    name: str = Field(..., description="Friendly name for the API key")
    key_type: Literal['publishable', 'secret'] = Field(..., description="Type of API key")
    environment: Literal['test', 'live'] = Field(default='test', description="Environment for the API key")


class APIKeyRes(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    merchant_id: str
    name: str
    key_type: str
    environment: str
    key_prefix: str
    is_active: bool
    created_at: datetime
    last_used_at: Optional[datetime]



class APIKeyFullRes(APIKeyRes):
    api_key: str


class APIKeyUpdate(BaseModel):
    name: str = Field(..., description="New friendly name for the API key")


class APIKeyRevoke(BaseModel):
    reason: Optional[str] = Field(default=None, description="Reason for revoking the key")


class WebhookEndpointCreate(BaseModel):
    url: HttpUrl = Field(..., description="Webhook endpoint URL")
    description: Optional[str] = Field(None, description="Description of the webhook")
    events: List[str] = Field(..., description="List of event types to subscribe to")
    enabled: bool = Field(default=True, description="Whether the webhook is enabled")
    api_version: Optional[str] = Field(default=None, description="API version for the webhook")


class WebhookEndpointRes(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    merchant_id: str
    url: str
    description: Optional[str]
    events: List[str]
    enabled: bool
    secret: str
    api_version: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]



class WebhookEndpointUpdate(BaseModel):
    url: Optional[HttpUrl] = None
    description: Optional[str] = None
    events: Optional[List[str]] = None
    enabled: Optional[bool] = None


class WebhookDelivery(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    webhook_endpoint_id: int
    event_type: str
    payload: dict
    response_status_code: Optional[int] = None
    response_body: Optional[str] = None
    attempt_number: int = Field(default=1)
    delivered_at: Optional[datetime] = None
    next_retry_at: Optional[datetime] = None



class WebhookDeliveryRes(WebhookDelivery):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    success: bool



class APIVersionInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    version: str
    release_date: datetime
    deprecated: bool = Field(default=False)
    sunset_date: Optional[datetime] = None


