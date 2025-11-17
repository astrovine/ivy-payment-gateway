from datetime import datetime, timezone

from fastapi import Depends, APIRouter, HTTPException, status, Request
from sqlalchemy.orm import Session

from ..models import db_models
from ..schemas import account as user_schema
from ..services.verification_service import VerificationService
from ..utilities import Oauth2 as au
from ..utilities.db_con import get_db
from ..utilities.exceptions import (
    UserAlreadyVerifiedError,
    VerificationError,
    UserNotFoundError,
)
from ..utilities.logger import log_user_action, setup_logger

router = APIRouter(prefix="/api/v1/verification", tags=["Business Verification"])
logger = setup_logger(__name__)


@router.post('/business', response_model=user_schema.UserVerRes, status_code=status.HTTP_201_CREATED)
async def submit_business_verification(
    verification_data: user_schema.UserVer,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user),
    request: Request = None
):
    """
    Submit business verification details (Step 2 of onboarding).
    Required after registration before creating a merchant account.
    """
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"User {current_user.id} submitting business verification from {ip_address}")

    try:
        verified = VerificationService.submit_business_verification(
            db=db,
            current_user=current_user,
            verification_data=verification_data
        )

        merchant_id = current_user.merchant_info.merchant_id if hasattr(current_user, 'merchant_info') and current_user.merchant_info else None
        log_user_action(
            db=db,
            user_id=current_user.id,
            action="BUSINESS_VERIFICATION_SUBMITTED",
            resource_type="USER_VERIFIED",
            resource_id=str(current_user.id),
            merchant_id=merchant_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            extra_data={
                "business_name": verification_data.business_name,
                "business_type": verification_data.business_type,
                "industry": verification_data.industry,
                "submitted_at": datetime.now(timezone.utc).isoformat()
            }
        )
        db.commit()

        logger.info(f"Business verification submitted successfully for user {current_user.id} - {verification_data.business_name}")
        return verified

    except UserAlreadyVerifiedError:
        logger.warning(f"User {current_user.id} attempted to submit verification when already verified")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Business verification already submitted"
        )
    except VerificationError as e:
        db.rollback()
        logger.error(f"Verification failed for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during business verification for user {current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not submit business verification"
        )


@router.get('/business', response_model=user_schema.UserVerifiedInfoRes, status_code=status.HTTP_200_OK)
async def get_business_verification_status(
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user),
    request: Request = None
):
    """
    Get the current business verification status and details.
    Returns 404 if no verification has been submitted.
    """
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"User {current_user.id} requesting business verification status from {ip_address}")

    try:
        verification = VerificationService.get_business_verification_status(
            db=db,
            current_user=current_user
        )

        if not verification:
            logger.info(f"No business verification found for user {current_user.id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No business verification found"
            )

        merchant_id = current_user.merchant_info.merchant_id if hasattr(current_user, 'merchant_info') and current_user.merchant_info else None
        log_user_action(
            db=db,
            user_id=current_user.id,
            action="BUSINESS_VERIFICATION_STATUS_VIEWED",
            resource_type="USER_VERIFIED",
            resource_id=str(current_user.id),
            merchant_id=merchant_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            extra_data={
                "business_name": verification.get("business_name"),
                "verification_status": verification.get("verification_status"),
                "viewed_at": datetime.now(timezone.utc).isoformat()
            }
        )
        db.commit()

        logger.info(f"Business verification status retrieved for user {current_user.id} - {verification.get('business_name')} - Status: {verification.get('verification_status')}")
        return verification

    except HTTPException:
        raise
    except VerificationError as e:
        logger.error(f"Error retrieving verification status for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error retrieving verification status for user {current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not retrieve business verification status"
        )


@router.put('/business', response_model=user_schema.UserVerifiedInfoRes, status_code=status.HTTP_200_OK)
async def update_business_information(
    update_data: user_schema.UserUpdateVer,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user),
    request: Request = None
):
    """
    Update business verification information.
    Only available if business verification has already been submitted.
    """
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"User {current_user.id} updating business information from {ip_address}")

    try:
        updated_verification = VerificationService.update_business_information(
            db=db,
            current_user=current_user,
            update_data=update_data
        )

        merchant_id = current_user.merchant_info.merchant_id if hasattr(current_user, 'merchant_info') and current_user.merchant_info else None
        log_user_action(
            db=db,
            user_id=current_user.id,
            action="BUSINESS_INFORMATION_UPDATED",
            resource_type="USER_VERIFIED",
            resource_id=str(current_user.id),
            merchant_id=merchant_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            changes=update_data.model_dump(exclude_unset=True),
            extra_data={
                "business_name": updated_verification.get("business_name"),
                "verification_status": updated_verification.get("verification_status"),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
        )
        db.commit()

        logger.info(f"Business information updated successfully for user {current_user.id}")
        return updated_verification

    except UserNotFoundError as e:
        logger.warning(f"User {current_user.id} attempted to update non-existent business verification")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except VerificationError as e:
        db.rollback()
        logger.error(f"Error updating business information for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error updating business information for user {current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not update business information"
        )

