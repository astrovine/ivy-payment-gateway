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

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])
logger = setup_logger(__name__)


@router.put('/merchants/{merchant_id}/limits', response_model=mer.TransactionLimitsRes)
async def update_merchant_limits(
        merchant_id: str,
        limits_data: mer.TransactionLimits,
        request: Request,
        db: Session = Depends(get_db),
        admin_user: db_models.User = Depends(au.get_current_superadmin)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"Admin {admin_user.email} updating limits for merchant {merchant_id} from {ip_address}")

    updated_limits = MerchantService.update_limits(
        db=db,
        merchant_id=merchant_id,
        limits_data=limits_data
    )

    if not updated_limits:
        logger.warning(f"Admin {admin_user.id} attempted to update limits for non-existent merchant {merchant_id}")
        raise HTTPException(status_code=404, detail="Merchant or limits not found.")

    log_user_action(
        db=db,
        user_id=admin_user.id,
        action="ADMIN_UPDATE_MERCHANT_LIMITS",
        resource_type="MERCHANT",
        resource_id=merchant_id,
        merchant_id=merchant_id,
        ip_address=ip_address,
        user_agent=request.headers.get("user-agent") if request else None,
        changes=limits_data.model_dump(exclude_unset=True),
        extra_data={
            "admin_email": admin_user.email,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }
    )
    db.commit()
    logger.info(f"Admin {admin_user.email} successfully updated limits for merchant {merchant_id}")

    return updated_limits
