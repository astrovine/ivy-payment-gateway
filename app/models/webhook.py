from .base import (
    Base, Column, Integer, String, Boolean, DateTime, ForeignKey, func
)


class WebhookEndpoint(Base):
    __tablename__ = "webhook_endpoints"

    id = Column(Integer, primary_key=True, autoincrement=True)
    merchant_id = Column(String, ForeignKey("merchant_accounts.merchant_id", ondelete="CASCADE"), nullable=False)

    url = Column(String, nullable=False)
    description = Column(String, nullable=True)
    events = Column(String, nullable=False)
    secret = Column(String, nullable=False)
    enabled = Column(Boolean, nullable=False, default=True)
    api_version = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class WebhookDelivery(Base):
    __tablename__ = "webhook_deliveries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    webhook_id = Column(Integer, ForeignKey("webhook_endpoints.id", ondelete="CASCADE"), nullable=False, index=True)
    event = Column(String, nullable=False)
    payload = Column(String, nullable=True)
    status = Column(String, nullable=False, default="pending")
    http_status = Column(Integer, nullable=True)
    response_body = Column(String, nullable=True)
    attempts = Column(Integer, nullable=False, default=0)
    last_attempt_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
