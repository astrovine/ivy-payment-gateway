from fastapi import APIRouter, Depends, HTTPException, status, Request, Response, Header
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Optional

from ..schemas import charges as charge_schema
from ..services.payment_service import ChargeService
from ..utilities.db_con import get_db
from ..utilities import Oauth2 as au
from ..models import db_models
from ..utilities.exceptions import ChargeCreationError
from ..utilities.logger import setup_logger, log_user_action, log_security_event

router = APIRouter(prefix="/v1/charges", tags=["Charges"])
logger = setup_logger(__name__)

@router.post("/", response_model=charge_schema.ChargeResponse, status_code=status.HTTP_201_CREATED)
async def create_new_charge(
    charge_data: charge_schema.ChargeCreate,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user_or_api_key),
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    x_idempotency_key: Optional[str] = Header(None, alias="X-Idempotency-Key")
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"User {current_user.id} ({current_user.email}) initiated charge creation from {ip_address}")

    final_idempotency_key = idempotency_key or x_idempotency_key or charge_data.idempotency_key

    if final_idempotency_key:
        charge_data.idempotency_key = final_idempotency_key
        logger.info(f"Using idempotency key: {final_idempotency_key} for charge creation")

    try:
        new_charge = ChargeService.create_charge(db=db, user=current_user, charge_data=charge_data)

        merchant_id = current_user.merchant_info.merchant_id if hasattr(current_user, 'merchant_info') and current_user.merchant_info else None
        log_user_action(
            db=db,
            user_id=current_user.id,
            action="CHARGE_CREATED",
            resource_type="CHARGE",
            resource_id=new_charge.id,
            merchant_id=merchant_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            extra_data={
                "charge_id": new_charge.id,
                "amount": str(new_charge.amount),
                "currency": new_charge.currency,
                "status": new_charge.status,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        )
        db.commit()

        response.headers["Location"] = f"/v1/charges/{new_charge.id}"

        logger.info(f"Charge {new_charge.id} created successfully for user {current_user.id}")
        return new_charge

    except ChargeCreationError as e:
        logger.error(f"Failed to create charge for user {current_user.id}: {str(e)}", exc_info=True)
        log_security_event(
            "CHARGE_CREATION_FAILED",
            {
                "user_id": current_user.id,
                "email": current_user.email,
                "error": str(e),
                "ip_address": ip_address
            },
            severity="WARNING"
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.critical(f"Unexpected error in create charge endpoint for user {current_user.id}: {e}", exc_info=True)
        log_security_event(
            "CHARGE_CREATION_ERROR",
            {
                "user_id": current_user.id,
                "email": current_user.email,
                "error": str(e),
                "ip_address": ip_address
            },
            severity="ERROR"
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal server error occurred.")


@router.get("/", response_model=list[charge_schema.ChargeResponse])
async def list_charges(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user)
):
    charges = db.query(db_models.Charge).filter_by(user_id=current_user.id).order_by(db_models.Charge.created_at.desc()).offset(skip).limit(limit).all()
    return charges


@router.get("/{charge_id}", response_model=charge_schema.ChargeResponse)
async def get_charge(
    charge_id: str,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user)
):
    charge = db.query(db_models.Charge).filter_by(id=charge_id, user_id=current_user.id).first()
    if not charge:
        raise HTTPException(status_code=status.HTTP_44_NOT_FOUND, detail="Charge not found")
    return charge