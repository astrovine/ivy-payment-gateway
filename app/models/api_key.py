from .base import (
    Base, Column, Integer, String, Boolean, DateTime, ForeignKey, TIMESTAMP, func
)


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, autoincrement=True)
    merchant_id = Column(String, ForeignKey("merchant_accounts.merchant_id", ondelete="CASCADE"), nullable=False)

    name = Column(String, nullable=False)
    api_key = Column(String, nullable=False, unique=True)
    key_prefix = Column(String, nullable=False)
    key_type = Column(String, nullable=False)
    environment = Column(String, nullable=False, default="test")

    is_active = Column(Boolean, nullable=False, default=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    revoked_at = Column(TIMESTAMP(timezone=True), nullable=True)
    revoke_reason = Column(String, nullable=True)
