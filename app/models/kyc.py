from .base import (
    Base, relationship, Column, Integer, String, Boolean, DateTime, ForeignKey, SAEnum, TIMESTAMP, func
)
from .enums import KYCStatus, RiskLevel


class KYCDocument(Base):
    __tablename__ = "kyc_documents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    document_type = Column(String, nullable=False)
    file_url = Column(String, nullable=False)
    file_name = Column(String, nullable=False)
    description = Column(String, nullable=True)

    status = Column(String, nullable=False, default="pending")
    rejection_reason = Column(String, nullable=True)

    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    reviewed_at = Column(TIMESTAMP(timezone=True), nullable=True)
    reviewed_by = Column(String, nullable=True)


class KYCVerification(Base):
    __tablename__ = "kyc_verifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)

    kyc_status = Column(SAEnum(KYCStatus, name="kyc_verification_status_enum"), nullable=False,
                        default=KYCStatus.not_started)
    submitted_at = Column(TIMESTAMP(timezone=True), nullable=True)
    verified_at = Column(TIMESTAMP(timezone=True), nullable=True)
    rejection_reason = Column(String, nullable=True)
    required_actions = Column(String, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    merchant_info = relationship(
        "MerchantAccount",
        primaryjoin="foreign(KYCVerification.user_id) == MerchantAccount.user_id",
        back_populates="kyc_info",
        uselist=False,
    )


class IdentityVerification(Base):
    __tablename__ = "identity_verifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)

    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    date_of_birth = Column(DateTime(timezone=True), nullable=False)
    id_number = Column(String, nullable=False)
    id_type = Column(String, nullable=False)
    id_country = Column(String, nullable=False)
    address_line1 = Column(String, nullable=False)
    address_line2 = Column(String, nullable=True)
    city = Column(String, nullable=False)
    state_province = Column(String, nullable=False)
    postal_code = Column(String, nullable=False)
    country = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    merchant_info = relationship(
        "MerchantAccount",
        primaryjoin="foreign(IdentityVerification.user_id) == MerchantAccount.user_id",
        back_populates="identity_info",
        uselist=False,
    )


class BusinessVerification(Base):
    __tablename__ = "business_verifications"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)

    legal_business_name = Column(String, nullable=False)
    trading_name = Column(String, nullable=True)
    business_registration_number = Column(String, nullable=False)
    tax_id = Column(String, nullable=False)
    business_type = Column(String, nullable=False)
    incorporation_date = Column(DateTime(timezone=True), nullable=False)
    incorporation_country = Column(String, nullable=False)
    business_address_line1 = Column(String, nullable=False)
    business_address_line2 = Column(String, nullable=True)
    business_city = Column(String, nullable=False)
    business_state_province = Column(String, nullable=False)
    business_postal_code = Column(String, nullable=False)
    business_country = Column(String, nullable=False)
    website = Column(String, nullable=True)
    business_description = Column(String, nullable=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    merchant_info = relationship(
        "MerchantAccount",
        primaryjoin="foreign(BusinessVerification.user_id) == MerchantAccount.user_id",
        back_populates="business_info",
        uselist=False,
    )


class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    merchant_id = Column(String, ForeignKey("merchant_accounts.merchant_id", ondelete="CASCADE"), nullable=False)

    risk_level = Column(SAEnum(RiskLevel, name="risk_assessment_level_enum"), nullable=False)
    risk_factors = Column(String, nullable=True)
    review_required = Column(Boolean, nullable=False, default=False)
    notes = Column(String, nullable=True)
    assessed_by = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    assessed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
