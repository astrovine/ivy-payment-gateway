from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form, Request
from sqlalchemy.orm import Session
from ..utilities.db_con import get_db
from ..utilities import Oauth2 as au
from ..models import db_models
from ..schemas import kyc as kyc_schema
from ..services.kyc_service import KycService
from ..utilities.exceptions import VerificationError, DatabaseError, KYCRequiredError
from ..utilities.logger import setup_logger, log_user_action, log_security_event

logger = setup_logger(__name__)
router = APIRouter(prefix="/api/v1/kyc", tags=["kyc"])


@router.post("/documents", response_model=kyc_schema.KYCDocumentRes, status_code=status.HTTP_201_CREATED)
async def upload_kyc_document(
        request: Request,
        db: Session = Depends(get_db),
        current_user: db_models.User = Depends(au.get_current_user),
        document_type: str = Form(...),
        file: UploadFile = File(...),
        file_name: str = Form(...),
        description: Optional[str] = Form(None)
):
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent") if request else None
    logger.info(f"KYC document upload attempt by user {current_user.id} ({current_user.email}) - Document type: {document_type} from IP: {ip_address}")

    if not current_user.merchant_info:
        logger.warning(f"User {current_user.id} has no merchant account, cannot upload KYC docs.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Merchant account not found. Please create one first.")

    document_data = kyc_schema.KYCDocumentUpload(
        document_type=document_type,
        file_name=file_name,
        description=description
    )

    try:
        new_kyc = KycService.upload_kyc_documents(
            db=db,
            document_data=document_data,
            file=file,
            merchant=current_user.merchant_info
        )

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="KYC_DOCUMENT_UPLOADED",
            resource_type="KYC_DOCUMENT",
            resource_id=str(new_kyc.id),
            merchant_id=current_user.merchant_info.merchant_id if current_user.merchant_info else None,
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data={
                "document_type": document_type,
                "file_name": file_name,
                "email": current_user.email
            }
        )
        db.commit()
        logger.info(f"KYC document uploaded successfully by user {current_user.id} ({current_user.email}) - Document ID: {new_kyc.id}, Type: {document_type}")
        return new_kyc

    except (VerificationError, DatabaseError) as e:
        db.rollback()
        logger.error(f"KYC document upload error for user {current_user.id} ({current_user.email}): {str(e)}")
        log_security_event(
            "KYC_UPLOAD_ERROR",
            {"user_id": current_user.id, "email": current_user.email, "error": str(e), "ip_address": ip_address},
            severity="ERROR"
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in KYC document upload for user {current_user.id} ({current_user.email}): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="An internal server error occurred.")


@router.get('/documents', status_code=status.HTTP_200_OK, response_model=List[kyc_schema.KYCDocumentRes])
async def get_kyc_documents(request: Request, db: Session = Depends(get_db), current_user: db_models.User = Depends(au.get_current_user)):
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent") if request else None
    logger.info(f"User {current_user.id} ({current_user.email}) retrieving all KYC documents from IP: {ip_address}")

    try:
        merchant_documents = db.query(db_models.KYCDocument).filter(db_models.KYCDocument.user_id == current_user.id).all()

        if not merchant_documents:
            logger.info(f"No KYC documents found for user {current_user.id} ({current_user.email})")
            return []

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="KYC_DOCUMENTS_VIEWED",
            resource_type="KYC_DOCUMENT",
            merchant_id=current_user.merchant_info.merchant_id if current_user.merchant_info else None,
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data={
                "email": current_user.email,
                "documents_count": len(merchant_documents)
            }
        )
        db.commit()
        logger.info(f"User {current_user.id} ({current_user.email}) retrieved {len(merchant_documents)} KYC documents")
        return merchant_documents

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error in getting KYC documents for user {current_user.id} ({current_user.email}): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred")


@router.get('/documents/{id}', status_code=status.HTTP_200_OK, response_model=kyc_schema.KYCDocumentRes)
async def get_specific_document(id: int, request: Request, db: Session = Depends(get_db), current_user: db_models.User = Depends(au.get_current_user)):
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent") if request else None
    logger.info(f"User {current_user.id} ({current_user.email}) retrieving KYC document {id} from IP: {ip_address}")

    try:
        document_asked_for = KycService.get_kyc_document_by_id(db=db, document_id=id, user=current_user)

        if not document_asked_for:
            logger.warning(f"KYC document {id} not found for user {current_user.id} ({current_user.email})")
            log_security_event(
                "KYC_DOCUMENT_ACCESS_DENIED",
                {"user_id": current_user.id, "email": current_user.email, "document_id": id, "ip_address": ip_address},
                severity="WARNING"
            )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KYC document not found")

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="KYC_DOCUMENT_VIEWED",
            resource_type="KYC_DOCUMENT",
            resource_id=str(document_asked_for.id),
            merchant_id=current_user.merchant_info.merchant_id if current_user.merchant_info else None,
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data={
                "email": current_user.email,
                "document_type": document_asked_for.document_type,
                "file_name": document_asked_for.file_name
            }
        )
        db.commit()
        logger.info(f"User {current_user.id} ({current_user.email}) successfully retrieved KYC document {id} - Type: {document_asked_for.document_type}")
        return document_asked_for

    except (KYCRequiredError, DatabaseError) as e:
        db.rollback()
        logger.warning(f"KYC document {id} access error for user {current_user.id} ({current_user.email}): {str(e)}")
        log_security_event(
            "KYC_DOCUMENT_ACCESS_ERROR",
            {"user_id": current_user.id, "email": current_user.email, "document_id": id, "error": str(e), "ip_address": ip_address},
            severity="WARNING"
        )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KYC document not found or access denied")
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error retrieving KYC document {id} for user {current_user.id} ({current_user.email}): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred")

@router.delete('/documents/{id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_kyc_document(id: int, request: Request, db:Session = Depends(get_db), current_user: db_models.User = Depends(au.get_current_user)):
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent") if request else None
    logger.info(f"User {current_user.id} ({current_user.email}) request to delete KYC document {id} from IP: {ip_address}")

    try:
        document = db.query(db_models.KYCDocument).filter(
            db_models.KYCDocument.id == id,
            db_models.KYCDocument.user_id == current_user.id
        ).first()

        if not document:
            logger.warning(f"KYC document {id} not found for user {current_user.id} ({current_user.email})")
            log_security_event(
                "KYC_DOCUMENT_DELETE_FAILED",
                {"user_id": current_user.id, "email": current_user.email, "document_id": id, "ip_address": ip_address, "reason": "not_found"},
                severity="WARNING"
            )
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="KYC document not found")

        document_type = document.document_type
        file_name = document.file_name

        KycService.delete_kyc_document(db=db, document_id=id, user=current_user)

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="KYC_DOCUMENT_DELETED",
            resource_type="KYC_DOCUMENT",
            resource_id=str(id),
            merchant_id=current_user.merchant_info.merchant_id if current_user.merchant_info else None,
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data={
                "email": current_user.email,
                "document_type": document_type,
                "file_name": file_name
            }
        )
        db.commit()
        logger.info(f"User {current_user.id} ({current_user.email}) successfully deleted KYC document {id} - Type: {document_type}")

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error deleting KYC document {id} for user {current_user.id} ({current_user.email}): {e}", exc_info=True)
        log_security_event(
            "KYC_DOCUMENT_DELETE_ERROR",
            {"user_id": current_user.id, "email": current_user.email, "document_id": id, "error": str(e), "ip_address": ip_address},
            severity="ERROR"
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete KYC document")


@router.post('/submit', response_model=kyc_schema.KYCVerificationRes, status_code=status.HTTP_200_OK)
async def submit_kyc_for_review(
    request: Request,
    verification_request: kyc_schema.KYCVerificationRequest,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user)
):
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent") if request else None
    logger.info(f"User {current_user.id} ({current_user.email}) submitting KYC for review from IP: {ip_address}")

    try:
        kyc_verification = KycService.submit_kyc_for_review(
            db=db,
            user=current_user,
            document_ids=verification_request.document_ids
        )

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="KYC_SUBMITTED_FOR_REVIEW",
            resource_type="KYC_VERIFICATION",
            resource_id=str(kyc_verification.id),
            merchant_id=current_user.merchant_info.merchant_id if current_user.merchant_info else None,
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data={
                "email": current_user.email,
                "document_count": len(verification_request.document_ids),
                "document_ids": verification_request.document_ids
            }
        )
        db.commit()

        logger.info(f"KYC submitted for review successfully for user {current_user.id}")
        return kyc_verification

    except VerificationError as e:
        db.rollback()
        logger.error(f"KYC submission failed for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error submitting KYC for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to submit KYC for review")


@router.get('/status', response_model=kyc_schema.KYCVerificationRes, status_code=status.HTTP_200_OK)
async def get_kyc_status(
    request: Request,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user)
):
    ip_address = request.client.host if request.client else "unknown"
    logger.info(f"User {current_user.id} ({current_user.email}) requesting KYC status from IP: {ip_address}")

    try:
        status_data = KycService.get_kyc_status(db=db, user=current_user)
        logger.info(f"KYC status retrieved for user {current_user.id}: {status_data['kyc_status']}")
        return status_data

    except Exception as e:
        logger.error(f"Unexpected error retrieving KYC status for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve KYC status")


@router.get('/required-actions', status_code=status.HTTP_200_OK)
async def get_required_actions(
    request: Request,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user)
):
    ip_address = request.client.host if request.client else "unknown"
    logger.info(f"User {current_user.id} ({current_user.email}) requesting required KYC actions from IP: {ip_address}")

    try:
        actions = KycService.get_required_actions(db=db, user=current_user)
        logger.info(f"Required KYC actions retrieved for user {current_user.id}: {len(actions['required_actions'])} actions")
        return actions

    except Exception as e:
        logger.error(f"Unexpected error retrieving required actions for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve required actions")


@router.post('/identity', status_code=status.HTTP_201_CREATED, response_model=kyc_schema.IdentityVerificationRes)
async def submit_identity_verification(
    request: Request,
    identity_data: kyc_schema.IdentityVerification,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user)
):
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent") if request else None
    logger.info(f"User {current_user.id} ({current_user.email}) submitting identity verification from IP: {ip_address}")

    try:
        identity_dict = identity_data.model_dump()
        identity = KycService.create_or_update_identity(
            db=db,
            user_id=current_user.id,
            data=identity_data
        )

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="IDENTITY_VERIFICATION_SUBMITTED",
            resource_type="IDENTITY_VERIFICATION",
            resource_id=str(identity.id),
            merchant_id=current_user.merchant_info.merchant_id if current_user.merchant_info else None,
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data={"email": current_user.email, "id_type": identity_data.id_type}
        )
        db.commit()

        logger.info(f"Identity verification submitted successfully for user {current_user.id}")
        return identity

    except VerificationError as e:
        db.rollback()
        logger.error(f"Identity verification failed for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error submitting identity verification for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to submit identity verification")

@router.get(
    "/identity",
    response_model=kyc_schema.IdentityVerificationRes
)
async def get_identity_verification(
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user)
):
    identity = KycService.get_identity(db=db, user_id=current_user.id)
    if not identity:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Identity information not found.")
    return identity

@router.post('/business', status_code=status.HTTP_201_CREATED, response_model=kyc_schema.BusinessVerificationRes)
async def submit_business_verification_details(
    request: Request,
    business_data: kyc_schema.BusinessVerification,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user)
):
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent") if request else None
    logger.info(f"User {current_user.id} ({current_user.email}) submitting business verification from IP: {ip_address}")

    try:
        business = KycService.create_or_update_business(
            db=db,
            user_id=current_user.id,
            data=business_data
        )

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="BUSINESS_VERIFICATION_SUBMITTED",
            resource_type="BUSINESS_VERIFICATION",
            resource_id=str(business.id),
            merchant_id=current_user.merchant_info.merchant_id if current_user.merchant_info else None,
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data={"email": current_user.email, "legal_business_name": business_data.legal_business_name}
        )
        db.commit()

        logger.info(f"Business verification submitted successfully for user {current_user.id}")
        return business

    except VerificationError as e:
        db.rollback()
        logger.error(f"Business verification failed for user {current_user.id}: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error submitting business verification for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to submit business verification")

@router.get(
    "/business",
    response_model=kyc_schema.BusinessVerificationRes
)
async def get_business_verification(
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user)
):
    business = KycService.get_business(db=db, user_id=current_user.id)
    if not business:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business information not found.")
    return business