from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from ..schemas import payout as payout_schema
from ..services.payout_service import PayoutService, PayoutAccountService
from ..services.merchant_service import MerchantService
from ..utilities.db_con import get_db
from ..utilities import Oauth2 as au
from ..models import db_models
from ..utilities.exceptions import PayoutError, MerchantAccountNotFoundError, DatabaseError
from ..utilities.logger import setup_logger, log_user_action
from ..services.notification_service import NotificationService

router = APIRouter(prefix="/api/v1/payouts", tags=["Payouts"])
logger = setup_logger(__name__)


@router.post("/", response_model=payout_schema.PayoutRes, status_code=status.HTTP_201_CREATED)
async def create_payout(
        payout_data: payout_schema.PayoutCreate,
        request: Request,
        db: Session = Depends(get_db),
        current_user: db_models.User = Depends(au.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"Payout creation request for user {current_user.email} from {ip_address}")
    try:
        # resolve payout account and call service with explicit args
        account = PayoutAccountService.get_payout_account(db=db, user=current_user, account_id=payout_data.payout_account_id)
        new_payout = PayoutService.create_payout(db=db, user_id=current_user.id, amount=payout_data.amount, currency=payout_data.currency, account=account)

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="PAYOUT_CREATED",
            resource_type="PAYOUT",
            resource_id=str(new_payout.id),
            merchant_id=new_payout.merchant_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            extra_data={"amount": str(new_payout.amount), "currency": new_payout.currency}
        )
        db.commit()
        try:
            NotificationService.create_notification(db=db, merchant_id=new_payout.merchant_id, user_id=current_user.id, type='payout.created', message=f"Payout requested: {new_payout.amount} {new_payout.currency}", data=str({"payout_id": new_payout.id}))
        except Exception:
            logger.exception("Failed to create notification for new payout")
        return new_payout
    except (PayoutError, MerchantAccountNotFoundError) as e:
        db.rollback()
        logger.warning(f"Failed to create payout for {current_user.email}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating payout for {current_user.email}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="An internal server error occurred.")


@router.get("/", response_model=List[payout_schema.PayoutRes])
async def list_payouts(
        request: Request,
        db: Session = Depends(get_db),
        current_user: db_models.User = Depends(au.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"Listing payouts for user {current_user.email} from {ip_address}")
    try:
        payouts = PayoutService.list_payouts(db=db, user_id=current_user.id)
        return payouts
    except (MerchantAccountNotFoundError, DatabaseError) as e:
        logger.error(f"Error listing payouts: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{payout_id}", response_model=payout_schema.PayoutRes)
async def get_payout(
        payout_id: int,
        request: Request,
        db: Session = Depends(get_db),
        current_user: db_models.User = Depends(au.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"Fetching payout {payout_id} for user {current_user.email} from {ip_address}")
    try:
        merchant = MerchantService.get_merchant_account(db=db, user_id=current_user.id)
        payout = PayoutService.get_payout(db=db, user_id=current_user.id, payout_id=payout_id)
        if not payout:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payout not found")
        return payout
    except MerchantAccountNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant account not found")


@router.put("/{payout_id}/cancel", response_model=payout_schema.PayoutRes)
async def cancel_payout(
        payout_id: int,
        request: Request,
        db: Session = Depends(get_db),
        current_user: db_models.User = Depends(au.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"Cancellation request for payout {payout_id} by {current_user.email} from {ip_address}")
    try:
        merchant = MerchantService.get_merchant_account(db=db, user_id=current_user.id)
        payout = PayoutService.cancel_payout(db=db, user_id=current_user.id, payout_id=payout_id)

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="PAYOUT_CANCELLED",
            resource_type="PAYOUT",
            resource_id=str(payout.id),
            merchant_id=payout.merchant_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            extra_data={"amount": str(payout.amount), "currency": payout.currency}
        )
        db.commit()
        try:
            NotificationService.create_notification(db=db, merchant_id=payout.merchant_id, user_id=current_user.id, type='payout.cancelled', message=f"Payout cancelled: {payout.amount} {payout.currency}", data=str({"payout_id": payout.id}))
        except Exception:
            logger.exception("Failed to create notification for payout cancellation")
        return payout
    except MerchantAccountNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant account not found")
    except PayoutError as e:
        db.rollback()
        logger.warning(f"Failed to cancel payout {payout_id} for {current_user.email}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))