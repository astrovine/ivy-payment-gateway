from datetime import datetime
import cloudinary
import cloudinary.uploader
from cloudinary.exceptions import Error as CloudinaryError
from fastapi import UploadFile
from sqlalchemy.orm import Session
from app.schemas import kyc
from ..models import db_models
from ..utilities.exceptions import MerchantAccountNotFoundError, PermissionDeniedError, \
    VerificationError, KYCRequiredError
from ..utilities.logger import setup_logger

logger = setup_logger(__name__)


class KycService:
    @staticmethod
    def upload_kyc_documents(
            db: Session,
            document_data: kyc.KYCDocumentUpload,
            file: UploadFile,
            merchant: db_models.MerchantAccount
    ):
        try:
            logger.info(
                f'Processing KYC document upload for merchant {merchant.merchant_id} - Document type: {document_data.document_type}, File: {document_data.file_name}')
            db_merchant = db.query(db_models.MerchantAccount).filter(
                db_models.MerchantAccount.merchant_id == merchant.merchant_id
            ).first()

            if not db_merchant:
                logger.warning(f'Merchant account {merchant.merchant_id} not found during KYC document upload')
                raise MerchantAccountNotFoundError

            existing_doc = db.query(db_models.KYCDocument).filter(
                db_models.KYCDocument.user_id == db_merchant.user_id,
                db_models.KYCDocument.document_type == document_data.document_type
            ).first()

            if existing_doc:
                logger.warning(
                    f'KYC document type {document_data.document_type} already exists for merchant {merchant.merchant_id} (user ID: {db_merchant.user_id})')
                raise PermissionDeniedError("Document type already uploaded.")

            logger.info(f'Uploading file to Cloudinary for merchant {merchant.merchant_id}')
            upload_result = cloudinary.uploader.upload(
                file.file,
                folder=f"kyc_documents/{db_merchant.merchant_id}",
                resource_type="auto"
            )

            file_url = upload_result.get("secure_url")
            if not file_url:
                logger.error(
                    f"Cloudinary upload succeeded but no secure_url returned for merchant {merchant.merchant_id}")
                raise CloudinaryError("Upload succeeded but no secure_url returned.")
            logger.info(
                f"KYC file successfully uploaded to Cloudinary for merchant {db_merchant.merchant_id}: {file_url}")

            new_document = db_models.KYCDocument(
                user_id=db_merchant.user_id,
                document_type=document_data.document_type,
                file_url=file_url,
                file_name=document_data.file_name,
                description=document_data.description if document_data.description else None,
                uploaded_at=datetime.now(),
                status="pending"
            )
            db.add(new_document)

            kyc_status = db.query(db_models.KYCVerification).filter_by(
                user_id=db_merchant.user_id
            ).first()

            if not kyc_status:
                logger.info(
                    f'Creating new KYC verification record with not_started status for user {db_merchant.user_id}')
                kyc_status = db_models.KYCVerification(
                    user_id=db_merchant.user_id,
                    kyc_status=db_models.KYCStatus.not_started
                )
                db.add(kyc_status)

            db.commit()
            db.refresh(new_document)
            logger.info(
                f"KYC document {new_document.id} successfully saved to database - Type: {document_data.document_type}, File: {document_data.file_name}, Merchant: {merchant.merchant_id}, User: {db_merchant.user_id}")

            return new_document

        except CloudinaryError as e:
            db.rollback()
            logger.error(
                f"Cloudinary upload failed for merchant {merchant.merchant_id} - Document type: {document_data.document_type}, Error: {e}")
            raise VerificationError(reason="File upload provider error.")
        except (MerchantAccountNotFoundError, PermissionDeniedError) as e:
            db.rollback()
            logger.warning(f'KYC upload failed for merchant {merchant.merchant_id} - {type(e).__name__}: {e}')
            raise e
        except Exception as e:
            db.rollback()
            logger.error(
                f'Unexpected error during KYC document upload for merchant {merchant.merchant_id} - Document type: {document_data.document_type}, Error: {e}',
                exc_info=True)
            raise e

    @staticmethod
    def get_kyc_document_by_id(db: Session, document_id: int, user: db_models.User) -> db_models.KYCDocument:
        logger.info(f'User {user.id} ({user.email}) attempting to retrieve KYC document {document_id}')
        document = db.query(db_models.KYCDocument).filter(
            db_models.KYCDocument.id == document_id,
            db_models.KYCDocument.user_id == user.id
        ).first()
        if not document:
            logger.warning(f'KYC document {document_id} not found or access denied for user {user.id} ({user.email})')
            raise KYCRequiredError("Document not found")
        return document

    @staticmethod
    def delete_kyc_document(db: Session, document_id: int, user: db_models.User):
        logger.info(f'{user.email} attempting to delete KYC document {document_id}')

        document = db.query(db_models.KYCDocument).filter(
            db_models.KYCDocument.id == document_id,
            db_models.KYCDocument.user_id == user.id
        ).first()

        if not document:
            logger.warning(f'KYC document {document_id} not found for deletion by user {user.id}')
            raise KYCRequiredError("Document not found")

        db.delete(document)
        db.commit()
        logger.info(f'KYC document {document_id} deleted by user {user.id}')

    @staticmethod
    def submit_kyc_for_review(db: Session, user: db_models.User, document_ids: list[int]):
        try:
            logger.info(f'User {user.id} ({user.email}) submitting KYC for review with document IDs: {document_ids}')

            documents = db.query(db_models.KYCDocument).filter(
                db_models.KYCDocument.user_id == user.id,
                db_models.KYCDocument.id.in_(document_ids)
            ).all()

            if len(documents) != len(document_ids):
                logger.warning(
                    f'Some documents not found for user {user.id}. Requested: {document_ids}, Found: {[d.id for d in documents]}')
                raise VerificationError("Some documents not found")

            identity = db.query(db_models.IdentityVerification).filter_by(user_id=user.id).first()
            business = db.query(db_models.BusinessVerification).filter_by(user_id=user.id).first()

            if not identity or not business:
                logger.warning(f'KYC submission failed for user {user.id}: Missing identity or business information.')
                raise VerificationError("Missing required identity or business information.")

            kyc_verification = db.query(db_models.KYCVerification).filter_by(user_id=user.id).first()
            if not kyc_verification:
                kyc_verification = db_models.KYCVerification(
                    user_id=user.id,
                    kyc_status=db_models.KYCStatus.pending,
                    submitted_at=datetime.now()
                )
                db.add(kyc_verification)
            else:
                kyc_verification.kyc_status = db_models.KYCStatus.pending
                kyc_verification.submitted_at = datetime.now()

            merchant = db.query(db_models.MerchantAccount).filter_by(user_id=user.id).first()
            if merchant:
                merchant.kyc_status = db_models.KYCStatus.pending
                logger.info(f'Updated merchant {merchant.merchant_id} KYC status to pending')

            db.commit()
            db.refresh(kyc_verification)
            logger.info(f'KYC submitted for review successfully for user {user.id}')
            return kyc_verification

        except Exception as e:
            db.rollback()
            logger.error(f'Error submitting KYC for user {user.id}: {e}', exc_info=True)
            raise

    @staticmethod
    def get_kyc_status(db: Session, user: db_models.User):
        logger.info(f'Fetching KYC status for user {user.id} ({user.email})')
        kyc_verification = db.query(db_models.KYCVerification).filter_by(user_id=user.id).first()

        if not kyc_verification:
            logger.info(f'No KYC verification found for user {user.id}, returning default status')
            return {
                "user_id": user.id,
                "kyc_status": "not_started",
                "submitted_at": None,
                "verified_at": None,
                "rejection_reason": None,
                "required_actions": None
            }

        logger.info(f'KYC status for user {user.id}: {kyc_verification.kyc_status.name}')
        return {
            "user_id": kyc_verification.user_id,
            "kyc_status": kyc_verification.kyc_status.name,
            "submitted_at": kyc_verification.submitted_at,
            "verified_at": kyc_verification.verified_at,
            "rejection_reason": kyc_verification.rejection_reason,
            "required_actions": kyc_verification.required_actions.split(
                ',') if kyc_verification.required_actions else None
        }

    @staticmethod
    def get_required_actions(db: Session, user: db_models.User):
        logger.info(f'Fetching required KYC actions for user {user.id}')

        documents = db.query(db_models.KYCDocument).filter_by(user_id=user.id).all()
        identity = db.query(db_models.IdentityVerification).filter_by(user_id=user.id).first()
        business = db.query(db_models.BusinessVerification).filter_by(user_id=user.id).first()

        actions = []

        if not identity:
            actions.append("Submit identity verification")
        if not business:
            actions.append("Submit business verification details")

        required_docs = ['business_registration', 'identity_proof', 'address_proof']
        uploaded_types = [d.document_type for d in documents]

        for doc_type in required_docs:
            if doc_type not in uploaded_types:
                actions.append(f"Upload {doc_type.replace('_', ' ')}")

        logger.info(f'Required actions for user {user.id}: {actions}')
        return {"required_actions": actions}

    @staticmethod
    def create_or_update_identity(db: Session, user_id: int, data: kyc.IdentityVerification):
        logger.info(f'Creating or updating identity verification for user {user_id}')
        identity = db.query(db_models.IdentityVerification).filter_by(user_id=user_id).first()

        data_dict = data.model_dump()

        if identity:
            for key, value in data_dict.items():
                setattr(identity, key, value)
            logger.info(f'Updated existing identity verification for user {user_id}')
        else:
            identity = db_models.IdentityVerification(user_id=user_id, **data_dict)
            db.add(identity)
            logger.info(f'Created new identity verification for user {user_id}')

        db.commit()
        db.refresh(identity)
        return identity

    @staticmethod
    def get_identity(db: Session, user_id: int):
        logger.info(f'Fetching identity verification for user {user_id}')
        return db.query(db_models.IdentityVerification).filter_by(user_id=user_id).first()

    @staticmethod
    def create_or_update_business(db: Session, user_id: int, data: kyc.BusinessVerification):
        logger.info(f'Creating or updating business verification for user {user_id}')
        business = db.query(db_models.BusinessVerification).filter_by(user_id=user_id).first()

        data_dict = data.model_dump()
        if 'website' in data_dict and data_dict['website']:
            data_dict['website'] = str(data_dict['website'])

        if business:
            for key, value in data_dict.items():
                setattr(business, key, value)
            logger.info(f'Updated existing business verification for user {user_id}')
        else:
            business = db_models.BusinessVerification(user_id=user_id, **data_dict)
            db.add(business)
            logger.info(f'Created new business verification for user {user_id}')

        db.commit()
        db.refresh(business)
        return business

    @staticmethod
    def get_business(db: Session, user_id: int):
        logger.info(f'Fetching business verification for user {user_id}')
        return db.query(db_models.BusinessVerification).filter_by(user_id=user_id).first()