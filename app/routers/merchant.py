from datetime import datetime, timezone
from typing import List

from fastapi import Depends, APIRouter, HTTPException, status, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ..models import db_models
from ..schemas import merchant as mer, ledger
from ..services.merchant_service import  MerchantService
from ..utilities import Oauth2 as au
from ..utilities.db_con import get_db
from ..utilities.exceptions import VerificationError, DatabaseError
from ..utilities.logger import log_user_action, log_security_event, setup_logger

logger = setup_logger(__name__)
router = APIRouter(prefix="/api/v1/merchant", tags=["Merchant"])

@router.post('/account', response_model=mer.MerchantAccountRes, status_code=status.HTTP_201_CREATED)
async def create_merchant(data:mer.MerchantAccountCreate, request: Request, db: Session = Depends(get_db), current_user: db_models.User = Depends(au.get_current_user)):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"User {current_user.id} ({current_user.name}) initiated merchant account creation from {ip_address}")

    try:
        if not current_user.verified_info:
            logger.warning(f"Unverified user {current_user.id} ({current_user.name}) attempted to create merchant account from {ip_address}")
            log_security_event(
                "UNVERIFIED_MERCHANT_CREATION_ATTEMPT",
                {"user_id": current_user.id, "email": current_user.email, "ip_address": ip_address},
                severity="WARNING"
            )
            raise VerificationError('Please Verify your account first')
        user = db.query(db_models.UserVerified).filter(db_models.UserVerified.user_id == current_user.id).first()


        new_merchant = MerchantService.create_merchant_account(db=db, data=data, user_id=current_user.id)

        log_user_action(
            db=db,
            user_id=current_user.id,
            action='MERCHANT_ACCOUNT_CREATED',
            resource_type='MERCHANT',
            resource_id=new_merchant.merchant_id,
            merchant_id=new_merchant.merchant_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            extra_data={
                "merchant_id": new_merchant.merchant_id,
                "business_name": user.business_name,
                "business_type": user.business_type.value if hasattr(user.business_type, 'value') else str(user.business_type),
                "settlement_schedule": new_merchant.settlement_schedule,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        )
        db.commit()
        logger.info(f"Merchant account {new_merchant.merchant_id} created successfully for user {current_user.id}")
        return new_merchant

    except VerificationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IntegrityError as e:
        db.rollback()
        logger.warning(f"Duplicate merchant account attempt for user {current_user.id} from {ip_address}: {e}")
        log_security_event(
            "DUPLICATE_MERCHANT_CREATION_ATTEMPT",
            {"user_id": current_user.id, "email": current_user.email, "ip_address": ip_address},
            severity="WARNING"
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                            detail="A merchant account for this user already exists.")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating merchant account for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred.")


@router.get('/account', response_model=mer.MerchantAccountRes, status_code=status.HTTP_200_OK)
async def get_merchant(request: Request, db: Session = Depends(get_db), current_user: db_models.User = Depends(au.get_current_user)):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"User {current_user.id} ({current_user.name}) requesting merchant account details from {ip_address}")

    try:
        if not current_user.verified_info:
            logger.warning(f"Unverified user {current_user.id} attempted to access merchant account from {ip_address}")
            log_security_event(
                "UNVERIFIED_MERCHANT_ACCESS_ATTEMPT",
                {"user_id": current_user.id, "email": current_user.email, "ip_address": ip_address},
                severity="WARNING"
            )
            raise VerificationError('Please Verify your account first')

        merchant_details = MerchantService.get_merchant_account(db=db, user_id=current_user.id)

        if merchant_details is None:
            logger.warning(f"User {current_user.id} has no merchant account found")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant account not found")

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="MERCHANT_ACCOUNT_VIEWED",
            resource_type="MERCHANT",
            resource_id=merchant_details.merchant_id,
            merchant_id=merchant_details.merchant_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            extra_data={
                "merchant_id": merchant_details.merchant_id,
                "viewed_at": datetime.now(timezone.utc).isoformat()
            }
        )
        db.commit()
        logger.info(f"User {current_user.id} retrieved merchant account {merchant_details.merchant_id} successfully")
        return merchant_details

    except VerificationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving merchant account for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve merchant account")


@router.put('/account', response_model=mer.MerchantAccountRes, status_code=status.HTTP_200_OK)
async def update_merchant_account(data: mer.MerchantAccountUpdate, request: Request, db: Session = Depends(get_db), current_user: db_models.User = Depends(au.get_current_user)):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"User {current_user.id} ({current_user.name}) updating merchant account from {ip_address}")

    try:
        if not current_user.verified_info:
            logger.warning(f"Unverified user {current_user.id} attempted to update merchant account from {ip_address}")
            log_security_event(
                "UNVERIFIED_MERCHANT_UPDATE_ATTEMPT",
                {"user_id": current_user.id, "email": current_user.email, "ip_address": ip_address},
                severity="WARNING"
            )
            raise VerificationError('Please Verify your account first')

        updated_merchant = MerchantService.update_merchant_account(data=data, db=db, user_id=current_user.id)
        updated_merchant.updated_at = datetime.now(timezone.utc)

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="MERCHANT_ACCOUNT_UPDATED",
            resource_type="MERCHANT",
            resource_id=updated_merchant.merchant_id,
            merchant_id=updated_merchant.merchant_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            changes=data.model_dump(exclude_unset=True),
            extra_data={"updated_at": datetime.now(timezone.utc).isoformat()}
        )
        db.commit()
        logger.info(f"Merchant account {updated_merchant.merchant_id} updated successfully for user {current_user.id}")
        return updated_merchant

    except VerificationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except IntegrityError as e:
        db.rollback()
        logger.error(f"IntegrityError updating merchant account for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid data provided")
    except DatabaseError as e:
        db.rollback()
        logger.error(f"Database error updating merchant account for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Database error occurred")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error updating merchant account for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update merchant account")


@router.get('/balance', response_model=mer.MerchantBalanceRes)
async def get_merchant_balance(request: Request, db: Session = Depends(get_db), current_user: db_models.User = Depends(au.get_current_user)):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"User {current_user.id} ({current_user.name}) requesting merchant balance from {ip_address}")

    try:
        if not current_user.verified_info:
            logger.warning(f"Unverified user {current_user.id} attempted to access merchant balance from {ip_address}")
            log_security_event(
                "UNVERIFIED_BALANCE_ACCESS_ATTEMPT",
                {"user_id": current_user.id, "email": current_user.email, "ip_address": ip_address},
                severity="WARNING"
            )
            raise VerificationError('Please Verify your account first')

        balance = MerchantService.get_merchant_balance(db=db, user_id=current_user.id)

        merchant = current_user.merchant_info
        resource_id = merchant.merchant_id if merchant else None

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="MERCHANT_BALANCE_VIEWED",
            resource_type="MERCHANT",
            resource_id=resource_id or "unknown",
            merchant_id=resource_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            extra_data={
                "merchant_id": resource_id or "unknown",
                "viewed_at": datetime.now(timezone.utc).isoformat()
            }
        )
        db.commit()
        logger.info(f"User {current_user.id} retrieved merchant balance successfully")
        return balance

    except VerificationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Error retrieving merchant balance for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve merchant balance")

@router.get('/balance/history', response_model=List[ledger.BalanceHistory], status_code=status.HTTP_200_OK)
async def get_merchant_balance_history(request: Request, db: Session = Depends(get_db), current_user: db_models.User = Depends(au.get_current_user)):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"Retrieving balance history for user:{current_user.id} ({current_user.name}) from {ip_address}")
    merchant = current_user.merchant_info
    if not current_user.verified_info or not merchant:
        logger.warning(f"User {current_user.id} attempted to get balance history but is not verified with a merchant account.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="Merchant account not found. Please create one first.")
    try:
        balance_history = MerchantService.get_merchant_balance_history(db=db, merchant_id=merchant.merchant_id)

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="BALANCE_HISTORY_VIEWED",
            resource_type="MERCHANT",
            resource_id=merchant.merchant_id,
            merchant_id=merchant.merchant_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            extra_data={"transaction_count": len(balance_history) if balance_history else 0}
        )
        db.commit()

        if not balance_history:
            logger.info(f'Could not find any balance for {merchant.merchant_id}')
            return []
        return balance_history
    except Exception as e:
        db.rollback()
        logger.error(f'Unexpected error occurred while getting balance history for {merchant.merchant_id}: {e}', exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get balance history")


@router.get('/limits', response_model=mer.TransactionLimitsRes, status_code=status.HTTP_200_OK)
async def get_my_limits(
        request: Request,
        db: Session = Depends(get_db),
        current_user: db_models.User = Depends(au.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"User {current_user.id} requesting transaction limits from {ip_address}")

    merchant = MerchantService.get_merchant_account(db=db, user_id=current_user.id)

    limits = db.query(db_models.TransactionLimit).filter(
        db_models.TransactionLimit.merchant_id == merchant.merchant_id
    ).first()

    if not limits:
        logger.warning(f"Transaction limits not found for merchant {merchant.merchant_id}")
        raise HTTPException(status_code=404, detail="Transaction limits not found.")

    log_user_action(
        db=db,
        user_id=current_user.id,
        action="TRANSACTION_LIMITS_VIEWED",
        resource_type="MERCHANT",
        resource_id=merchant.merchant_id,
        merchant_id=merchant.merchant_id,
        ip_address=ip_address,
        user_agent=request.headers.get("user-agent") if request else None,
        extra_data={"viewed_at": datetime.now(timezone.utc).isoformat()}
    )
    db.commit()
    logger.info(f"User {current_user.id} retrieved transaction limits successfully")

    return limits


@router.get('/fees', response_model=mer.FeeStructureRes, status_code=status.HTTP_200_OK)
async def get_fee_structure(
        request: Request,
        db: Session = Depends(get_db),
        current_user: db_models.User = Depends(au.get_current_user)
):

    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"User {current_user.id} requesting fee structure from {ip_address}")

    try:

        if not current_user.verified_info:
            logger.warning(f"Unverified user {current_user.id} attempted to access fee structure from {ip_address}")
            log_security_event(
                "UNVERIFIED_FEE_ACCESS_ATTEMPT",
                {"user_id": current_user.id, "email": current_user.email, "ip_address": ip_address},
                severity="WARNING"
            )
            raise VerificationError('Please verify your account first')

        fee_structure = MerchantService.get_fee_structure(db=db, user_id=current_user.id)

        merchant = current_user.merchant_info
        merchant_id = merchant.merchant_id if merchant else None

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="FEE_STRUCTURE_VIEWED",
            resource_type="MERCHANT",
            resource_id=merchant_id,
            merchant_id=merchant_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            extra_data={"viewed_at": datetime.now(timezone.utc).isoformat()}
        )
        db.commit()

        logger.info(f"User {current_user.id} retrieved fee structure successfully")
        return fee_structure

    except VerificationError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Error retrieving fee structure for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve fee structure"
        )


@router.get('/settings', response_model=mer.MerchantSettingsRes, status_code=status.HTTP_200_OK)
async def get_merchant_settings(
        request: Request,
        db: Session = Depends(get_db),
        current_user: db_models.User = Depends(au.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"User {current_user.id} requesting merchant settings from {ip_address}")

    try:
        if not current_user.verified_info:
            logger.warning(f"Unverified user {current_user.id} attempted to access merchant settings from {ip_address}")
            log_security_event(
                "UNVERIFIED_SETTINGS_ACCESS_ATTEMPT",
                {"user_id": current_user.id, "email": current_user.email, "ip_address": ip_address},
                severity="WARNING"
            )
            raise VerificationError('Please verify your account first')

        settings = MerchantService.get_merchant_settings(db=db, user_id=current_user.id)

        merchant = current_user.merchant_info
        merchant_id = merchant.merchant_id if merchant else None

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="MERCHANT_SETTINGS_VIEWED",
            resource_type="MERCHANT",
            resource_id=merchant_id,
            merchant_id=merchant_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            extra_data={"viewed_at": datetime.now(timezone.utc).isoformat()}
        )
        db.commit()

        logger.info(f"User {current_user.id} retrieved merchant settings successfully")
        return settings

    except VerificationError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Error retrieving merchant settings for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve merchant settings"
        )


@router.put('/settings', response_model=mer.MerchantSettingsRes, status_code=status.HTTP_200_OK)
async def update_merchant_settings(
        settings_data: mer.MerchantSettings,
        request: Request,
        db: Session = Depends(get_db),
        current_user: db_models.User = Depends(au.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"User {current_user.id} updating merchant settings from {ip_address}")

    try:
        if not current_user.verified_info:
            logger.warning(f"Unverified user {current_user.id} attempted to update merchant settings from {ip_address}")
            log_security_event(
                "UNVERIFIED_SETTINGS_UPDATE_ATTEMPT",
                {"user_id": current_user.id, "email": current_user.email, "ip_address": ip_address},
                severity="WARNING"
            )
            raise VerificationError('Please verify your account first')

        updated_settings = MerchantService.update_merchant_settings(
            db=db,
            user_id=current_user.id,
            settings_data=settings_data
        )

        merchant = current_user.merchant_info
        merchant_id = merchant.merchant_id if merchant else None

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="MERCHANT_SETTINGS_UPDATED",
            resource_type="MERCHANT",
            resource_id=merchant_id,
            merchant_id=merchant_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            changes=settings_data.model_dump(exclude_unset=True),
            extra_data={"updated_at": datetime.now(timezone.utc).isoformat()}
        )
        db.commit()

        logger.info(f"User {current_user.id} updated merchant settings successfully")
        return updated_settings

    except VerificationError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except DatabaseError as e:
        db.rollback()
        logger.error(f"Database error updating merchant settings for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database error occurred"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error updating merchant settings for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update merchant settings"
        )
