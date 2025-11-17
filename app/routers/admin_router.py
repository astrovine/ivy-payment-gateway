from typing import Optional

from fastapi import Depends, APIRouter, HTTPException, status, Request, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..models import db_models
from ..services.admin_service import AdminService
from ..schemas import admin as admin_schema
from ..utilities import Oauth2 as au
from ..utilities.db_con import get_db
from ..utilities.exceptions import (
    MerchantAccountNotFoundError,
    PermissionDeniedError,
    VerificationError,
)
from ..utilities.logger import log_user_action, log_security_event, setup_logger

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])
logger = setup_logger(__name__)


class StatusUpdate(BaseModel):
    status: str

class RiskUpdate(BaseModel):
    risk_level: str
    risk_factors: list[str] = []
    review_required: bool = False
    notes: Optional[str] = None

class KYCRejection(BaseModel):
    rejection_reason: str


@router.get('/merchants', response_model=admin_schema.MerchantsListResponse, status_code=status.HTTP_200_OK)
async def get_all_merchants(
    request: Request,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    search: Optional[str] = None
):
    ip_address = request.client.host if request.client else "unknown"
    logger.info(f"Admin {current_user.id} ({current_user.email}) requesting merchants list from IP: {ip_address}")

    try:
        AdminService.verify_admin(current_user)

        result = AdminService.get_all_merchants(db=db, skip=skip, limit=limit, search=search)

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="ADMIN_MERCHANTS_LIST_VIEWED",
            resource_type="MERCHANT_ACCOUNT",
            merchant_id=None,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            extra_data={"total_count": result["total"], "search": search}
        )
        db.commit()

        logger.info(f"Admin {current_user.id} retrieved {len(result['merchants'])} merchants")
        return result

    except PermissionDeniedError as e:
        logger.warning(f"Non-admin user {current_user.id} attempted to access merchants list")
        log_security_event(
            "UNAUTHORIZED_ADMIN_ACCESS_ATTEMPT",
            {"user_id": current_user.id, "email": current_user.email, "endpoint": "/admin/merchants", "ip_address": ip_address},
            severity="WARNING"
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching merchants list for admin {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve merchants")


@router.get('/merchants/{merchant_id}', status_code=status.HTTP_200_OK)
async def get_merchant_details(
    merchant_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user)
):
    ip_address = request.client.host if request.client else "unknown"
    logger.info(f"Admin {current_user.id} ({current_user.email}) requesting details for merchant {merchant_id} from IP: {ip_address}")

    try:
        AdminService.verify_admin(current_user)

        result = AdminService.get_merchant_by_id(db=db, merchant_id=merchant_id)

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="ADMIN_MERCHANT_DETAILS_VIEWED",
            resource_type="MERCHANT_ACCOUNT",
            resource_id=merchant_id,
            merchant_id=merchant_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None
        )
        db.commit()

        logger.info(f"Admin {current_user.id} retrieved details for merchant {merchant_id}")
        return result

    except PermissionDeniedError as e:
        logger.warning(f"Non-admin user {current_user.id} attempted to access merchant {merchant_id} details")
        log_security_event(
            "UNAUTHORIZED_ADMIN_ACCESS_ATTEMPT",
            {"user_id": current_user.id, "email": current_user.email, "endpoint": f"/admin/merchants/{merchant_id}", "ip_address": ip_address},
            severity="WARNING"
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except MerchantAccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching merchant {merchant_id} details for admin {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve merchant details")


@router.put('/merchants/{merchant_id}/status', status_code=status.HTTP_200_OK)
async def update_merchant_status(
    merchant_id: str,
    status_update: StatusUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user)
):
    ip_address = request.client.host if request.client else "unknown"
    logger.info(f"Admin {current_user.id} ({current_user.email}) updating merchant {merchant_id} status to {status_update.status} from IP: {ip_address}")

    try:
        merchant = AdminService.update_merchant_status(
            db=db,
            merchant_id=merchant_id,
            status=status_update.status,
            admin_user=current_user
        )

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="ADMIN_MERCHANT_STATUS_UPDATED",
            resource_type="MERCHANT_ACCOUNT",
            resource_id=merchant_id,
            merchant_id=merchant_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            changes={"status": status_update.status},
            extra_data={"new_status": status_update.status}
        )
        db.commit()

        logger.info(f"Admin {current_user.id} updated merchant {merchant_id} status to {status_update.status}")
        return merchant

    except PermissionDeniedError as e:
        logger.warning(f"Non-admin user {current_user.id} attempted to update merchant {merchant_id} status")
        log_security_event(
            "UNAUTHORIZED_ADMIN_ACTION_ATTEMPT",
            {"user_id": current_user.id, "email": current_user.email, "action": "update_merchant_status", "merchant_id": merchant_id, "ip_address": ip_address},
            severity="WARNING"
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except MerchantAccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating merchant {merchant_id} status for admin {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update merchant status")


@router.put('/merchants/{merchant_id}/risk', status_code=status.HTTP_200_OK)
async def update_risk_assessment(
    merchant_id: str,
    risk_update: RiskUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user)
):
    ip_address = request.client.host if request.client else "unknown"
    logger.info(f"Admin {current_user.id} ({current_user.email}) updating risk assessment for merchant {merchant_id} from IP: {ip_address}")

    try:
        risk_data = risk_update.model_dump()

        assessment = AdminService.update_risk_assessment(
            db=db,
            merchant_id=merchant_id,
            risk_data=risk_data,
            admin_user=current_user
        )

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="ADMIN_RISK_ASSESSMENT_UPDATED",
            resource_type="RISK_ASSESSMENT",
            resource_id=str(assessment.id),
            merchant_id=merchant_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            changes=risk_data,
            extra_data={"risk_level": risk_update.risk_level, "merchant_id": merchant_id}
        )
        db.commit()

        logger.info(f"Admin {current_user.id} updated risk assessment for merchant {merchant_id}")
        return assessment

    except PermissionDeniedError as e:
        logger.warning(f"Non-admin user {current_user.id} attempted to update risk assessment for merchant {merchant_id}")
        log_security_event(
            "UNAUTHORIZED_ADMIN_ACTION_ATTEMPT",
            {"user_id": current_user.id, "email": current_user.email, "action": "update_risk_assessment", "merchant_id": merchant_id, "ip_address": ip_address},
            severity="WARNING"
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except MerchantAccountNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating risk assessment for merchant {merchant_id} by admin {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update risk assessment")


@router.post('/kyc/{user_id}/approve', status_code=status.HTTP_200_OK)
async def approve_kyc(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user)
):
    ip_address = request.client.host if request.client else "unknown"
    logger.info(f"Admin {current_user.id} ({current_user.email}) approving KYC for user {user_id} from IP: {ip_address}")

    try:
        kyc_verification = AdminService.approve_kyc(
            db=db,
            user_id=user_id,
            admin_user=current_user
        )

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="ADMIN_KYC_APPROVED",
            resource_type="KYC_VERIFICATION",
            resource_id=str(kyc_verification.id),
            merchant_id=None,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            extra_data={"approved_user_id": user_id}
        )
        db.commit()

        logger.info(f"Admin {current_user.id} approved KYC for user {user_id}")
        return kyc_verification

    except PermissionDeniedError as e:
        logger.warning(f"Non-admin user {current_user.id} attempted to approve KYC for user {user_id}")
        log_security_event(
            "UNAUTHORIZED_ADMIN_ACTION_ATTEMPT",
            {"user_id": current_user.id, "email": current_user.email, "action": "approve_kyc", "target_user_id": user_id, "ip_address": ip_address},
            severity="WARNING"
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except VerificationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Error approving KYC for user {user_id} by admin {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to approve KYC")


@router.post('/kyc/{user_id}/reject', status_code=status.HTTP_200_OK)
async def reject_kyc(
    user_id: int,
    rejection: KYCRejection,
    request: Request,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user)
):
    ip_address = request.client.host if request.client else "unknown"
    logger.info(f"Admin {current_user.id} ({current_user.email}) rejecting KYC for user {user_id} from IP: {ip_address}")

    try:
        kyc_verification = AdminService.reject_kyc(
            db=db,
            user_id=user_id,
            rejection_reason=rejection.rejection_reason,
            admin_user=current_user
        )

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="ADMIN_KYC_REJECTED",
            resource_type="KYC_VERIFICATION",
            resource_id=str(kyc_verification.id),
            merchant_id=None,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            extra_data={"rejected_user_id": user_id, "rejection_reason": rejection.rejection_reason}
        )
        db.commit()

        logger.info(f"Admin {current_user.id} rejected KYC for user {user_id}")
        return kyc_verification

    except PermissionDeniedError as e:
        logger.warning(f"Non-admin user {current_user.id} attempted to reject KYC for user {user_id}")
        log_security_event(
            "UNAUTHORIZED_ADMIN_ACTION_ATTEMPT",
            {"user_id": current_user.id, "email": current_user.email, "action": "reject_kyc", "target_user_id": user_id, "ip_address": ip_address},
            severity="WARNING"
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except VerificationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Error rejecting KYC for user {user_id} by admin {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reject KYC")


@router.get('/transactions', response_model=admin_schema.TransactionsListResponse, status_code=status.HTTP_200_OK)
async def get_all_transactions(
    request: Request,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    merchant_id: Optional[str] = None
):
    ip_address = request.client.host if request.client else "unknown"
    logger.info(f"Admin {current_user.id} ({current_user.email}) requesting transactions from IP: {ip_address}")

    try:
        AdminService.verify_admin(current_user)

        result = AdminService.get_all_transactions(db=db, skip=skip, limit=limit, merchant_id=merchant_id)

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="ADMIN_TRANSACTIONS_VIEWED",
            resource_type="CHARGE",
            merchant_id=None,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            extra_data={"total_count": result["total"], "merchant_id_filter": merchant_id}
        )
        db.commit()

        logger.info(f"Admin {current_user.id} retrieved {len(result['transactions'])} transactions")
        return result

    except PermissionDeniedError as e:
        logger.warning(f"Non-admin user {current_user.id} attempted to access transactions")
        log_security_event(
            "UNAUTHORIZED_ADMIN_ACCESS_ATTEMPT",
            {"user_id": current_user.id, "email": current_user.email, "endpoint": "/admin/transactions", "ip_address": ip_address},
            severity="WARNING"
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching transactions for admin {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve transactions")


@router.get('/audit-logs', response_model=admin_schema.AuditLogsListResponse, status_code=status.HTTP_200_OK)
async def get_audit_logs(
    request: Request,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    user_id: Optional[int] = None,
    action: Optional[str] = None
):
    ip_address = request.client.host if request.client else "unknown"
    logger.info(f"Admin {current_user.id} ({current_user.email}) requesting audit logs from IP: {ip_address}")

    try:
        AdminService.verify_admin(current_user)

        result = AdminService.get_audit_logs(db=db, skip=skip, limit=limit, user_id=user_id, action=action)

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="ADMIN_AUDIT_LOGS_VIEWED",
            resource_type="AUDIT_LOG",
            merchant_id=None,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            extra_data={"total_count": result["total"], "user_id_filter": user_id, "action_filter": action}
        )
        db.commit()

        logger.info(f"Admin {current_user.id} retrieved {len(result['logs'])} audit logs")
        return result

    except PermissionDeniedError as e:
        logger.warning(f"Non-admin user {current_user.id} attempted to access audit logs")
        log_security_event(
            "UNAUTHORIZED_ADMIN_ACCESS_ATTEMPT",
            {"user_id": current_user.id, "email": current_user.email, "endpoint": "/admin/audit-logs", "ip_address": ip_address},
            severity="WARNING"
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching audit logs for admin {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve audit logs")


@router.post('/merchants/{merchant_id}/sync-balances', status_code=status.HTTP_200_OK)
async def sync_merchant_balances(
    merchant_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user)
):
    ip_address = request.client.host if request.client else "unknown"
    logger.info(f"Admin {current_user.id} syncing balances for merchant {merchant_id} from IP: {ip_address}")

    try:
        AdminService.verify_admin(current_user)

        from ..services.balance_service import BalanceService

        BalanceService.sync_balances_from_charges(db=db, merchant_id=merchant_id)

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="ADMIN_BALANCES_SYNCED",
            resource_type="MERCHANT_ACCOUNT",
            resource_id=merchant_id,
            merchant_id=merchant_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            extra_data={"merchant_id": merchant_id}
        )
        db.commit()

        logger.info(f"Admin {current_user.id} synced balances for merchant {merchant_id}")
        return {"message": "Balances synced successfully", "merchant_id": merchant_id}

    except PermissionDeniedError as e:
        logger.warning(f"Non-admin user {current_user.id} attempted to sync balances for merchant {merchant_id}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        db.rollback()
        logger.error(f"Error syncing balances for merchant {merchant_id} by admin {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to sync balances")


@router.post('/users/{user_id}/promote', status_code=status.HTTP_200_OK)
async def promote_user_to_admin(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user)
):
    ip_address = request.client.host if request.client else "unknown"
    logger.info(f"Admin {current_user.id} attempting to promote user {user_id} to admin from IP: {ip_address}")

    try:
        AdminService.verify_admin(current_user)

        target_user = db.query(db_models.User).filter_by(id=user_id).first()
        if not target_user:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        if target_user.is_superadmin:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is already an admin")

        target_user.is_superadmin = True
        db.commit()

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="USER_PROMOTED_TO_ADMIN",
            resource_type="USER",
            resource_id=str(user_id),
            merchant_id=None,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            extra_data={"promoted_user_email": target_user.email, "promoted_user_id": user_id}
        )
        db.commit()

        logger.info(f"Admin {current_user.id} promoted user {user_id} ({target_user.email}) to admin")
        return {"message": f"User {target_user.email} promoted to admin successfully", "user_id": user_id}

    except PermissionDeniedError as e:
        logger.warning(f"Non-admin user {current_user.id} attempted to promote user {user_id}")
        log_security_event(
            "UNAUTHORIZED_ADMIN_ACTION_ATTEMPT",
            {"user_id": current_user.id, "email": current_user.email, "action": "promote_user", "target_user_id": user_id, "ip_address": ip_address},
            severity="WARNING"
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error promoting user {user_id} by admin {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to promote user")


@router.get('/payouts', status_code=status.HTTP_200_OK)
async def admin_list_payouts(
    request: Request,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=1000),
    merchant_id: Optional[str] = None
):
    ip_address = request.client.host if request.client else "unknown"
    logger.info(f"Admin {current_user.id} requesting payouts from IP: {ip_address}")
    try:
        AdminService.verify_admin(current_user)
        result = AdminService.get_all_payouts(db=db, skip=skip, limit=limit, merchant_id=merchant_id)

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="ADMIN_PAYOUTS_VIEWED",
            resource_type="PAYOUT",
            merchant_id=merchant_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            extra_data={"total_count": result["total"], "merchant_id_filter": merchant_id}
        )
        db.commit()
        return result
    except PermissionDeniedError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching admin payouts: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve payouts")
