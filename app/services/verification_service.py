from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..models import db_models
from ..schemas import account as user_schema
from ..utilities.exceptions import (
    UserAlreadyVerifiedError,
    VerificationError,
    UserNotFoundError,
)
from ..utilities.logger import setup_logger

logger = setup_logger("payment_gateway.services.verification_service")


class VerificationService:
    @staticmethod
    def submit_business_verification(
        db: Session,
        current_user: db_models.User,
        verification_data: user_schema.UserVer
    ) -> db_models.UserVerified:
        try:
            logger.info(f"Submitting business verification for user: {current_user.id} ({current_user.email})")

            existing = db.query(db_models.UserVerified).filter(
                db_models.UserVerified.user_id == current_user.id
            ).first()

            if existing:
                logger.warning(f"User {current_user.id} already has business verification submitted")
                raise UserAlreadyVerifiedError()

            website_str = str(verification_data.business_website) if verification_data.business_website else None
            ver_data = verification_data.model_dump()
            ver_data["user_id"] = current_user.id
            ver_data['business_website'] = website_str

            new_verification = db_models.UserVerified(**ver_data)
            db.add(new_verification)
            db.flush()
            db.refresh(new_verification)

            merchant_account = db.query(db_models.MerchantAccount).filter(
                db_models.MerchantAccount.user_id == current_user.id
            ).first()

            if merchant_account:
                merchant_account.verification_status = db_models.VerificationStatus.pending
                db.flush()
                logger.info(f"Updated merchant account {merchant_account.merchant_id} verification_status to pending")

            logger.info(f"Business verification submitted successfully for user {current_user.id} - {verification_data.business_name}")
            return new_verification

        except UserAlreadyVerifiedError:
            raise
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error during business verification for user {current_user.id}: {str(e)}")
            raise VerificationError("Business email may already be in use")
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error during business verification for user {current_user.id}: {str(e)}", exc_info=True)
            raise VerificationError(str(e))

    @staticmethod
    def get_business_verification_status(
        db: Session,
        current_user: db_models.User
    ) -> Optional[dict]:
        try:
            logger.info(f"Fetching business verification status for user: {current_user.id}")

            verification = db.query(db_models.UserVerified).filter(
                db_models.UserVerified.user_id == current_user.id
            ).first()

            if not verification:
                logger.info(f"No business verification found for user {current_user.id}")
                return None

            merchant_account = db.query(db_models.MerchantAccount).filter(
                db_models.MerchantAccount.user_id == current_user.id
            ).first()

            verification_status = "unverified"
            if merchant_account and merchant_account.verification_status:
                verification_status = merchant_account.verification_status.value

            logger.info(f"Business verification found for user {current_user.id} - {verification.business_name} - Status: {verification_status}")

            result = {
                "industry": verification.industry,
                "staff_size": verification.staff_size,
                "business_name": verification.business_name,
                "business_type": verification.business_type.value if hasattr(verification.business_type, 'value') else verification.business_type,
                "business_email": verification.business_email,
                "business_website": verification.business_website,
                "business_description": verification.business_description,
                "location": verification.location,
                "phone_number": verification.phone_number,
                "support_email": verification.support_email,
                "support_phone": verification.support_phone,
                "bank_account_name": verification.bank_account_name,
                "bank_account_number": verification.bank_account_number,
                "bank_name": verification.bank_name,
                "bank_code": verification.bank_code,
                "tax_id": verification.tax_id,
                "verification_status": verification_status
            }

            return result

        except Exception as e:
            logger.error(f"Error fetching business verification for user {current_user.id}: {str(e)}", exc_info=True)
            raise VerificationError(f"Failed to retrieve verification status: {str(e)}")

    @staticmethod
    def update_business_information(
        db: Session,
        current_user: db_models.User,
        update_data: user_schema.UserUpdateVer
    ) -> dict:
        try:
            logger.info(f"Updating business information for user: {current_user.id}")

            verification_query = db.query(db_models.UserVerified).filter(
                db_models.UserVerified.user_id == current_user.id
            )
            verification = verification_query.first()

            if not verification:
                logger.warning(f"No business verification found for user {current_user.id}")
                raise UserNotFoundError("No business verification found. Please submit verification first.")

            update_dict = update_data.model_dump(exclude_unset=True)

            if 'business_website' in update_dict and update_dict['business_website']:
                update_dict['business_website'] = str(update_dict['business_website'])

            if update_dict:
                verification_query.update(update_dict, synchronize_session=False)
                db.flush()
                db.refresh(verification)
                logger.info(f"Business information updated successfully for user {current_user.id}")
            else:
                logger.info(f"No fields to update for user {current_user.id}")

            merchant_account = db.query(db_models.MerchantAccount).filter(
                db_models.MerchantAccount.user_id == current_user.id
            ).first()

            verification_status = "unverified"
            if merchant_account and merchant_account.verification_status:
                verification_status = merchant_account.verification_status.value

            result = {
                "industry": verification.industry,
                "staff_size": verification.staff_size,
                "business_name": verification.business_name,
                "business_type": verification.business_type.value if hasattr(verification.business_type, 'value') else verification.business_type,
                "business_email": verification.business_email,
                "business_website": verification.business_website,
                "business_description": verification.business_description,
                "location": verification.location,
                "phone_number": verification.phone_number,
                "support_email": verification.support_email,
                "support_phone": verification.support_phone,
                "bank_account_name": verification.bank_account_name,
                "bank_account_number": verification.bank_account_number,
                "bank_name": verification.bank_name,
                "bank_code": verification.bank_code,
                "tax_id": verification.tax_id,
                "verification_status": verification_status
            }

            return result

        except UserNotFoundError:
            raise
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error updating business info for user {current_user.id}: {str(e)}")
            raise VerificationError("Business email may already be in use")
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error updating business info for user {current_user.id}: {str(e)}", exc_info=True)
            raise VerificationError(f"Failed to update business information: {str(e)}")

