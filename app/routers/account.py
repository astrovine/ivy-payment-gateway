from datetime import datetime, timezone
from fastapi import Depends, APIRouter, HTTPException, status, Request
from sqlalchemy.orm import Session
from ..models import db_models
from ..schemas import account as user_schema
from ..services.user_service import UserService
from ..utilities import Oauth2 as au
from ..utilities import db_con
from ..utilities.db_con import get_db
from ..utilities.exceptions import (
    UserNotFoundError, InvalidCredentialsError, PasswordMismatchError, DatabaseError,
)
from ..utilities.logger import log_user_action, setup_logger

router = APIRouter(prefix="/api/v1/users", tags=["User Accont"])
logger = setup_logger(__name__)

@router.get('/me', response_model=user_schema.UserMeResponse, status_code=status.HTTP_200_OK)
async def get_current_users_detials(
    request: Request,
    current_user: db_models.User = Depends(au.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"Full profile request: {current_user.id} from {ip_address}")

    is_verified = current_user.verified_info is not None
    has_merchant = current_user.merchant_info is not None

    if not is_verified:
        onboarding_stage = "account_created"
    elif not has_merchant:
        onboarding_stage = "verified"
    else:
        onboarding_stage = "active"

    logger.info(
        f"Successfully returned full profile of user {current_user.id} (verified: {is_verified}) from {ip_address}")

    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "country": current_user.country,
        "created_at": current_user.created_at,
        "is_verified": is_verified,
        "has_merchant_account": has_merchant,
        "onboarding_stage": onboarding_stage,
        "is_superadmin": current_user.is_superadmin
    }


@router.get('/me/refresh', status_code=status.HTTP_200_OK)
async def refresh_user_data(
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user),
    request: Request = None
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"User {current_user.id} refreshing their data from {ip_address}")

    try:
        user = UserService.get_full_user_info(db=db, user_id=current_user.id)

        if not user:
            raise UserNotFoundError("User not found")

        is_verified = user.verified_info is not None
        has_merchant = user.merchant_info is not None

        if not is_verified:
            onboarding_stage = "account_created"
        elif not has_merchant:
            onboarding_stage = "verified"
        else:
            onboarding_stage = "active"

        user_data = {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "country": user.country,
            "is_superadmin": user.is_superadmin,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "is_verified": is_verified,
            "has_merchant_account": has_merchant,
            "onboarding_stage": onboarding_stage,
            "verified_info": user.verified_info,
            "merchant_info": user.merchant_info
        }

        logger.info(f"User {current_user.id} data refreshed successfully (admin: {user.is_superadmin}, verified: {is_verified}, merchant: {has_merchant})")
        return user_data

    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put('/me', response_model=user_schema.UserUpdateRes, status_code=status.HTTP_200_OK)
async def update_user_info(data: user_schema.UserUpdate, request: Request = None, db: Session = Depends(get_db), current_user: db_models.User = Depends(au.get_current_user)):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"User {current_user.id} updating profile from {ip_address}")

    try:
        updated = UserService.update_user_account(db=db, user_id=current_user.id, update_data=data)

        merchant_id = current_user.merchant_info.merchant_id if current_user.merchant_info else None
        log_user_action(
            db=db,
            user_id=current_user.id,
            action="PROFILE_UPDATED",
            resource_type="USER",
            resource_id=str(current_user.id),
            merchant_id=merchant_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            changes=data.model_dump(exclude_unset=True),
            extra_data={"updated_at": datetime.now(timezone.utc).isoformat()}
        )
        db.commit()
        logger.info(f"User {current_user.id} profile updated successfully")
        return updated
    except UserNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.put('/me/password', status_code=status.HTTP_200_OK)
async def change_password(
    data: user_schema.UserUpdatePassword,
    db: Session = Depends(db_con.get_db),
    current_user: db_models.User = Depends(au.get_current_user),
    request: Request = None
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"Password change request for user {current_user.id} from {ip_address}")

    try:
        UserService.change_user_password(
            db=db,
            user=current_user,
            old_password=data.old_password,
            new_password=data.password,
            confirm_password=data.confirm_password
        )

        merchant_id = current_user.merchant_info.merchant_id if current_user.merchant_info else None
        log_user_action(
            db=db,
            user_id=current_user.id,
            action="PASSWORD_CHANGED",
            resource_type="USER",
            resource_id=str(current_user.id),
            merchant_id=merchant_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            extra_data={"changed_at": datetime.now(timezone.utc).isoformat()}
        )
        db.commit()
        logger.info(f"Password changed successfully for user {current_user.id}")
        return {"message": "Password updated successfully"}

    except InvalidCredentialsError:
        logger.warning(f"Invalid old password provided for user {current_user.id}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect old password")
    except PasswordMismatchError:
        logger.warning(f"New password mismatch for user {current_user.id}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="New passwords do not match")
    except Exception as e:
        logger.error(f"Unexpected error changing password for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not change password")


@router.get('/me/activity', status_code=status.HTTP_200_OK)
async def user_activity(request: Request, db: Session = Depends(db_con.get_db), current_user: db_models.User = Depends(au.get_current_user)):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"User activity request for user {current_user.id} from IP {ip_address}")
    try:
        activity = UserService.get_activity_logs(db=db, user=current_user)
        if not activity:
            logger.warning(f"No activity logs for user {current_user.id} from ip {ip_address}")
            return []
        merchant_id = current_user.merchant_info.merchant_id if current_user.merchant_info else None
        log_user_action(
            db=db,
            user_id=current_user.id,
            action="ACTIVITY_LOGS",
            resource_type="USER",
            resource_id=str(current_user.id),
            merchant_id=merchant_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            changes=None,
            extra_data={"Requested_at": datetime.now(timezone.utc).isoformat()}
        )
        return activity
    except DatabaseError as e:
        logger.error(f"Error getting activity logs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error getting activity logs: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.delete('/me', status_code=status.HTTP_204_NO_CONTENT)
async def delete_me(request: Request = None, db: Session = Depends(get_db), current_user: db_models.User = Depends(au.get_current_user)):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"User {current_user.id} ({current_user.email}) requesting account deletion from {ip_address}")

    try:
        merchant_id = current_user.merchant_info.merchant_id if hasattr(current_user, 'merchant_info') and current_user.merchant_info else None
        user_email = current_user.email
        user_id = current_user.id

        log_user_action(
            db=db,
            user_id=user_id,
            action="ACCOUNT_DELETED",
            resource_type="USER",
            resource_id=str(user_id),
            merchant_id=merchant_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            extra_data={"email": user_email, "deleted_at": datetime.now(timezone.utc).isoformat()}
        )

        UserService.delete_user_account(db=db, user_id=user_id)
        db.commit()
        logger.info(f"User {user_id} ({user_email}) account deleted successfully")
    except UserNotFoundError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))