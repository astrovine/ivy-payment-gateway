from datetime import datetime
import cloudinary
import cloudinary.uploader
from cloudinary.exceptions import Error as CloudinaryError
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import kyc
from ..models import db_models
from ..utilities.exceptions import MerchantAccountNotFoundError, PermissionDeniedError, \
    VerificationError, KYCRequiredError
from ..utilities.logger import setup_logger

logger = setup_logger(__name__)


class KycService:
    @staticmethod
    async def upload_kyc_documents(
            db: AsyncSession,
            document_data: kyc.KYCDocumentUpload,
            file: UploadFile,
            merchant: db_models.MerchantAccount
    ):
        try:
            logger.info(f'Processing KYC document upload for merchant {merchant.merchant_id} - Document type: {document_data.document_type}, File: {document_data.file_name}')

            result = await db.execute(select(db_models.MerchantAccount).where(db_models.MerchantAccount.merchant_id == merchant.merchant_id))
            db_merchant = result.scalar_one_or_none()

            if not db_merchant:
                logger.warning(f'Merchant account {merchant.merchant_id} not found during KYC document upload')
                raise MerchantAccountNotFoundError

            existing_result = await db.execute(
                select(db_models.KYCDocument)
                .where(db_models.KYCDocument.user_id == db_merchant.user_id, db_models.KYCDocument.document_type == document_data.document_type)
            )
            existing_doc = existing_result.scalar_one_or_none()

            if existing_doc:
                logger.warning(f'KYC document type {document_data.document_type} already exists for merchant {merchant.merchant_id} (user ID: {db_merchant.user_id})')
                raise PermissionDeniedError("Document type already uploaded.")

            logger.info(f'Uploading file to Cloudinary for merchant {merchant.merchant_id}')
            upload_result = cloudinary.uploader.upload(
                file.file,
                folder=f"kyc_documents/{db_merchant.merchant_id}",
                resource_type="auto"
            )

            file_url = upload_result.get("secure_url")
            if not file_url:
                logger.error(f"Cloudinary upload succeeded but no secure_url returned for merchant {merchant.merchant_id}")
                raise CloudinaryError("Upload succeeded but no secure_url returned.")
            logger.info(f"KYC file successfully uploaded to Cloudinary for merchant {db_merchant.merchant_id}: {file_url}")

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

            kyc_result = await db.execute(select(db_models.KYCVerification).where(db_models.KYCVerification.user_id == db_merchant.user_id))
            kyc_status = kyc_result.scalar_one_or_none()

            if not kyc_status:
                logger.info(f'Creating new KYC verification record with not_started status for user {db_merchant.user_id}')
                kyc_status = db_models.KYCVerification(
                    user_id=db_merchant.user_id,
                    kyc_status=db_models.KYCStatus.not_started
                )
                db.add(kyc_status)

            await db.commit()
            await db.refresh(new_document)
            logger.info(f"KYC document {new_document.id} successfully saved to database - Type: {document_data.document_type}, File: {document_data.file_name}, Merchant: {merchant.merchant_id}, User: {db_merchant.user_id}")

            return new_document

        except CloudinaryError as e:
            await db.rollback()
            logger.error(f"Cloudinary upload failed for merchant {merchant.merchant_id} - Document type: {document_data.document_type}, Error: {e}")
            raise VerificationError(reason="File upload provider error.")
        except (MerchantAccountNotFoundError, PermissionDeniedError) as e:
            await db.rollback()
            logger.warning(f'KYC upload failed for merchant {merchant.merchant_id} - {type(e).__name__}: {e}')
            raise e
        except Exception as e:
            await db.rollback()
            logger.error(f'Unexpected error during KYC document upload for merchant {merchant.merchant_id} - Document type: {document_data.document_type}, Error: {e}', exc_info=True)
            raise e

    @staticmethod
    async def get_kyc_document_by_id(db: AsyncSession, document_id: int, user: db_models.User) -> db_models.KYCDocument:
        logger.info(f'User {user.id} ({user.email}) attempting to retrieve KYC document {document_id}')
        result = await db.execute(
            select(db_models.KYCDocument)
            .where(db_models.KYCDocument.id == document_id, db_models.KYCDocument.user_id == user.id)
        )
        document = result.scalar_one_or_none()
        if not document:
            logger.warning(f'KYC document {document_id} not found or access denied for user {user.id} ({user.email})')
            raise KYCRequiredError("Document not found")
        return document

    @staticmethod
    async def delete_kyc_document(db: AsyncSession, document_id: int, user: db_models.User):
        logger.info(f'{user.email} attempting to delete KYC document {document_id}')

        result = await db.execute(
            select(db_models.KYCDocument)
            .where(db_models.KYCDocument.id == document_id, db_models.KYCDocument.user_id == user.id)
        )
        document = result.scalar_one_or_none()

        if not document:
            logger.warning(f'KYC document {document_id} not found for deletion by user {user.id}')
            raise KYCRequiredError("Document not found")

        await db.delete(document)
        await db.commit()
        logger.info(f'KYC document {document_id} deleted by user {user.id}')

    @staticmethod
    async def submit_kyc_for_review(db: AsyncSession, user: db_models.User, document_ids: list[int]):
        try:
            logger.info(f'User {user.id} ({user.email}) submitting KYC for review with document IDs: {document_ids}')

            result = await db.execute(
                select(db_models.KYCDocument)
                .where(db_models.KYCDocument.user_id == user.id, db_models.KYCDocument.id.in_(document_ids))
            )
            documents = result.scalars().all()

            if len(documents) != len(document_ids):
                logger.warning(f'Some documents not found for user {user.id}. Requested: {document_ids}, Found: {[d.id for d in documents]}')
                raise VerificationError("Some documents not found")

            identity_result = await db.execute(select(db_models.IdentityVerification).where(db_models.IdentityVerification.user_id == user.id))
            identity = identity_result.scalar_one_or_none()

            business_result = await db.execute(select(db_models.BusinessVerification).where(db_models.BusinessVerification.user_id == user.id))
            business = business_result.scalar_one_or_none()

            if not identity or not business:
                logger.warning(f'KYC submission failed for user {user.id}: Missing identity or business information.')
                raise VerificationError("Missing required identity or business information.")

            kyc_result = await db.execute(select(db_models.KYCVerification).where(db_models.KYCVerification.user_id == user.id))
            kyc_verification = kyc_result.scalar_one_or_none()

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

            merchant_result = await db.execute(select(db_models.MerchantAccount).where(db_models.MerchantAccount.user_id == user.id))
            merchant = merchant_result.scalar_one_or_none()
            if merchant:
                merchant.kyc_status = db_models.KYCStatus.pending
                logger.info(f'Updated merchant {merchant.merchant_id} KYC status to pending')

            await db.commit()
            await db.refresh(kyc_verification)
            logger.info(f'KYC submitted for review successfully for user {user.id}')
            return kyc_verification

        except Exception as e:
            await db.rollback()
            logger.error(f'Error submitting KYC for user {user.id}: {e}', exc_info=True)
            raise

    @staticmethod
    async def get_kyc_status(db: AsyncSession, user: db_models.User):
        logger.info(f'Fetching KYC status for user {user.id} ({user.email})')
        result = await db.execute(select(db_models.KYCVerification).where(db_models.KYCVerification.user_id == user.id))
        kyc_verification = result.scalar_one_or_none()

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
            "required_actions": kyc_verification.required_actions.split(',') if kyc_verification.required_actions else None
        }

    @staticmethod
    async def get_required_actions(db: AsyncSession, user: db_models.User):
        logger.info(f'Fetching required KYC actions for user {user.id}')

        docs_result = await db.execute(select(db_models.KYCDocument).where(db_models.KYCDocument.user_id == user.id))
        documents = docs_result.scalars().all()

        identity_result = await db.execute(select(db_models.IdentityVerification).where(db_models.IdentityVerification.user_id == user.id))
        identity = identity_result.scalar_one_or_none()

        business_result = await db.execute(select(db_models.BusinessVerification).where(db_models.BusinessVerification.user_id == user.id))
        business = business_result.scalar_one_or_none()

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
    async def create_or_update_identity(db: AsyncSession, user_id: int, data: kyc.IdentityVerification):
        logger.info(f'Creating or updating identity verification for user {user_id}')
        result = await db.execute(select(db_models.IdentityVerification).where(db_models.IdentityVerification.user_id == user_id))
        identity = result.scalar_one_or_none()

        data_dict = data.model_dump()

        if identity:
            for key, value in data_dict.items():
                setattr(identity, key, value)
            logger.info(f'Updated existing identity verification for user {user_id}')
        else:
            identity = db_models.IdentityVerification(user_id=user_id, **data_dict)
            db.add(identity)
            logger.info(f'Created new identity verification for user {user_id}')

        await db.commit()
        await db.refresh(identity)
        return identity

    @staticmethod
    async def get_identity(db: AsyncSession, user_id: int):
        logger.info(f'Fetching identity verification for user {user_id}')
        result = await db.execute(select(db_models.IdentityVerification).where(db_models.IdentityVerification.user_id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def create_or_update_business(db: AsyncSession, user_id: int, data: kyc.BusinessVerification):
        logger.info(f'Creating or updating business verification for user {user_id}')
        result = await db.execute(select(db_models.BusinessVerification).where(db_models.BusinessVerification.user_id == user_id))
        business = result.scalar_one_or_none()

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

        await db.commit()
        await db.refresh(business)
        return business

    @staticmethod
    async def get_business(db: AsyncSession, user_id: int):
        logger.info(f'Fetching business verification for user {user_id}')
        result = await db.execute(select(db_models.BusinessVerification).where(db_models.BusinessVerification.user_id == user_id))
        return result.scalar_one_or_none()