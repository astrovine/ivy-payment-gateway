import uuid
from .base import (
    Base, relationship, Column, Integer, String, Boolean, TIMESTAMP,
    DateTime, ForeignKey, SAEnum, func
)
from .enums import BusinessType


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=False, unique=True)
    password = Column(String, nullable=False)
    country = Column(String, nullable=False)
    password_reset_token = Column(String, nullable=True)
    password_reset_expires = Column(TIMESTAMP(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superadmin = Column(Boolean, default=False, nullable=False)
    charges = relationship("Charge", back_populates="user")
    verified_info = relationship("UserVerified", back_populates="user", uselist=False)
    merchant_info = relationship("MerchantAccount", back_populates="user_info", uselist=False)


class UserVerified(Base):
    __tablename__ = "user_verified"
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, nullable=False)
    industry = Column(String, nullable=False)
    staff_size = Column(Integer, nullable=False)
    business_name = Column(String, nullable=False)
    business_type = Column(SAEnum(BusinessType, name="business_type_enum"), nullable=False)
    business_email = Column(String, nullable=True, unique=True)
    business_website = Column(String, nullable=True)
    business_description = Column(String, nullable=True)
    location = Column(String, nullable=False)
    phone_number = Column(String, nullable=False)
    support_email = Column(String, nullable=True)
    support_phone = Column(String, nullable=True)
    bank_account_name = Column(String, nullable=False)
    bank_account_number = Column(String, nullable=False)
    bank_name = Column(String, nullable=True)
    bank_code = Column(String, nullable=True)
    tax_id = Column(String, nullable=True)
    user = relationship("User", back_populates="verified_info")


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    refresh_token = Column(String, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(TIMESTAMP(timezone=True), nullable=False)
    revoked = Column(Boolean, nullable=False, default=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
