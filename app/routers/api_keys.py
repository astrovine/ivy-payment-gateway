from datetime import datetime, timezone
from typing import List

from fastapi import Depends, APIRouter, HTTPException, status, Request
from sqlalchemy.orm import Session

from ..models import db_models
from ..schemas import api_key as api_key_schema
from ..services.merchant_service import MerchantService
from ..utilities import Oauth2 as au
from ..utilities.db_con import get_db
from ..utilities.exceptions import (
    MerchantAccountNotFoundError,
    ResourceNotFoundError,
    DatabaseError,
    VerificationError
)
from ..utilities.logger import log_user_action, log_security_event, setup_logger

logger = setup_logger(__name__)
router = APIRouter(prefix="/api/v1/api-keys", tags=["API Keys"])


@router.post('', response_model=api_key_schema.APIKeyFullRes, status_code=status.HTTP_201_CREATED)
async def create_api_key(
        key_data: api_key_schema.APIKeyCreate,
        request: Request,
        db: Session = Depends(get_db),
        current_user: db_models.User = Depends(au.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"User {current_user.id} creating API key from {ip_address}")

    try:
        if not current_user.verified_info:
            logger.warning(f"Unverified user {current_user.id} attempted to create API key from {ip_address}")
            log_security_event(
                "UNVERIFIED_API_KEY_CREATION_ATTEMPT",
                {"user_id": current_user.id, "email": current_user.email, "ip_address": ip_address},
                severity="WARNING"
            )
            raise VerificationError('Please verify your account first')

        if not current_user.merchant_info:
            logger.warning(f"User {current_user.id} without merchant account attempted to create API key")
            raise MerchantAccountNotFoundError("Please create a merchant account first")

        # Create the API key
        api_key, raw_key = MerchantService.create_api_key(db=db, user_id=current_user.id, key_data=key_data)

        # Log the action
        log_user_action(
            db=db,
            user_id=current_user.id,
            action="API_KEY_CREATED",
            resource_type="API_KEY",
            resource_id=str(api_key.id),
            merchant_id=current_user.merchant_info.merchant_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            extra_data={
                "key_id": api_key.id,
                "key_type": api_key.key_type,
                "environment": api_key.environment,
                "name": api_key.name,
                "created_at": datetime.now(timezone.utc).isoformat()
            }
        )
        db.commit()

        logger.info(f"API key {api_key.id} created successfully for user {current_user.id}")

        return api_key_schema.APIKeyFullRes(
            id=api_key.id,
            merchant_id=api_key.merchant_id,
            name=api_key.name,
            key_type=api_key.key_type,
            environment=api_key.environment,
            key_prefix=api_key.key_prefix,
            is_active=api_key.is_active,
            created_at=api_key.created_at,
            last_used_at=api_key.last_used_at,
            api_key=raw_key
        )

    except VerificationError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except MerchantAccountNotFoundError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DatabaseError as e:
        db.rollback()
        logger.error(f"Database error creating API key for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create API key")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error creating API key for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred")


@router.get('', response_model=List[api_key_schema.APIKeyRes], status_code=status.HTTP_200_OK)
async def list_api_keys(
        request: Request,
        db: Session = Depends(get_db),
        current_user: db_models.User = Depends(au.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"User {current_user.id} listing API keys from {ip_address}")

    try:
        if not current_user.verified_info:
            logger.warning(f"Unverified user {current_user.id} attempted to list API keys from {ip_address}")
            log_security_event(
                "UNVERIFIED_API_KEY_ACCESS_ATTEMPT",
                {"user_id": current_user.id, "email": current_user.email, "ip_address": ip_address},
                severity="WARNING"
            )
            raise VerificationError('Please verify your account first')

        if not current_user.merchant_info:
            logger.warning(f"User {current_user.id} without merchant account attempted to list API keys")
            raise MerchantAccountNotFoundError("Please create a merchant account first")

        api_keys = MerchantService.get_api_keys(db=db, user_id=current_user.id)

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="API_KEYS_LISTED",
            resource_type="API_KEY",
            merchant_id=current_user.merchant_info.merchant_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            extra_data={"count": len(api_keys)}
        )
        db.commit()

        logger.info(f"User {current_user.id} retrieved {len(api_keys)} API keys")
        return api_keys

    except VerificationError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except MerchantAccountNotFoundError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DatabaseError as e:
        db.rollback()
        logger.error(f"Database error listing API keys for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve API keys")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error listing API keys for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred")


@router.get('/{key_id}', response_model=api_key_schema.APIKeyRes, status_code=status.HTTP_200_OK)
async def get_api_key(
        key_id: int,
        request: Request,
        db: Session = Depends(get_db),
        current_user: db_models.User = Depends(au.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"User {current_user.id} getting API key {key_id} from {ip_address}")

    try:
        if not current_user.verified_info:
            logger.warning(f"Unverified user {current_user.id} attempted to access API key from {ip_address}")
            log_security_event(
                "UNVERIFIED_API_KEY_ACCESS_ATTEMPT",
                {"user_id": current_user.id, "email": current_user.email, "ip_address": ip_address},
                severity="WARNING"
            )
            raise VerificationError('Please verify your account first')

        if not current_user.merchant_info:
            logger.warning(f"User {current_user.id} without merchant account attempted to access API key")
            raise MerchantAccountNotFoundError("Please create a merchant account first")
        api_key = MerchantService.get_api_key_by_id(db=db, user_id=current_user.id, key_id=key_id)
        log_user_action(
            db=db,
            user_id=current_user.id,
            action="API_KEY_VIEWED",
            resource_type="API_KEY",
            resource_id=str(key_id),
            merchant_id=current_user.merchant_info.merchant_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            extra_data={"key_id": key_id, "key_name": api_key.name}
        )
        db.commit()

        logger.info(f"User {current_user.id} retrieved API key {key_id}")
        return api_key

    except VerificationError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except (MerchantAccountNotFoundError, ResourceNotFoundError) as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DatabaseError as e:
        db.rollback()
        logger.error(f"Database error getting API key {key_id} for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to retrieve API key")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error getting API key {key_id} for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred")


@router.put('/{key_id}', response_model=api_key_schema.APIKeyRes, status_code=status.HTTP_200_OK)
async def update_api_key(
        key_id: int,
        update_data: api_key_schema.APIKeyUpdate,
        request: Request,
        db: Session = Depends(get_db),
        current_user: db_models.User = Depends(au.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"User {current_user.id} updating API key {key_id} from {ip_address}")

    try:
        if not current_user.verified_info:
            logger.warning(f"Unverified user {current_user.id} attempted to update API key from {ip_address}")
            log_security_event(
                "UNVERIFIED_API_KEY_UPDATE_ATTEMPT",
                {"user_id": current_user.id, "email": current_user.email, "ip_address": ip_address},
                severity="WARNING"
            )
            raise VerificationError('Please verify your account first')

        if not current_user.merchant_info:
            logger.warning(f"User {current_user.id} without merchant account attempted to update API key")
            raise MerchantAccountNotFoundError("Please create a merchant account first")

        # Update the API key
        api_key = MerchantService.update_api_key(db=db, user_id=current_user.id, key_id=key_id, update_data=update_data)

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="API_KEY_UPDATED",
            resource_type="API_KEY",
            resource_id=str(key_id),
            merchant_id=current_user.merchant_info.merchant_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            changes={"name": update_data.name},
            extra_data={"key_id": key_id, "new_name": update_data.name}
        )
        db.commit()

        logger.info(f"User {current_user.id} updated API key {key_id}")
        return api_key

    except VerificationError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except (MerchantAccountNotFoundError, ResourceNotFoundError) as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DatabaseError as e:
        db.rollback()
        logger.error(f"Database error updating API key {key_id} for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update API key")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error updating API key {key_id} for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred")


@router.delete('/{key_id}', response_model=api_key_schema.APIKeyRes, status_code=status.HTTP_200_OK)
async def revoke_api_key(
        key_id: int,
        revoke_data: api_key_schema.APIKeyRevoke,
        request: Request,
        db: Session = Depends(get_db),
        current_user: db_models.User = Depends(au.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"User {current_user.id} revoking API key {key_id} from {ip_address}")

    try:
        if not current_user.verified_info:
            logger.warning(f"Unverified user {current_user.id} attempted to revoke API key from {ip_address}")
            log_security_event(
                "UNVERIFIED_API_KEY_REVOKE_ATTEMPT",
                {"user_id": current_user.id, "email": current_user.email, "ip_address": ip_address},
                severity="WARNING"
            )
            raise VerificationError('Please verify your account first')

        if not current_user.merchant_info:
            logger.warning(f"User {current_user.id} without merchant account attempted to revoke API key")
            raise MerchantAccountNotFoundError("Please create a merchant account first")

        # Revoke the API key
        api_key = MerchantService.revoke_api_key(
            db=db,
            user_id=current_user.id,
            key_id=key_id,
            reason=revoke_data.reason
        )

        log_security_event(
            event_type="API_KEY_REVOKED",
            details={
                "user_id": current_user.id,
                "key_id": key_id,
                "merchant_id": current_user.merchant_info.merchant_id,
                "reason": revoke_data.reason or "Not specified",
                "ip_address": ip_address
            },
            severity="INFO"
        )

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="API_KEY_REVOKED",
            resource_type="API_KEY",
            resource_id=str(key_id),
            merchant_id=current_user.merchant_info.merchant_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            extra_data={
                "key_id": key_id,
                "reason": revoke_data.reason or "Not specified",
                "revoked_at": datetime.now(timezone.utc).isoformat()
            }
        )
        db.commit()

        logger.info(f"User {current_user.id} revoked API key {key_id}")
        return api_key

    except VerificationError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except (MerchantAccountNotFoundError, ResourceNotFoundError) as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DatabaseError as e:
        db.rollback()
        logger.error(f"Database error revoking API key {key_id} for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to revoke API key")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error revoking API key {key_id} for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred")


@router.post('/{key_id}/roll', response_model=api_key_schema.APIKeyFullRes, status_code=status.HTTP_200_OK)
async def roll_api_key(
        key_id: int,
        request: Request,
        db: Session = Depends(get_db),
        current_user: db_models.User = Depends(au.get_current_user)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"User {current_user.id} rolling API key {key_id} from {ip_address}")

    try:

        if not current_user.verified_info:
            logger.warning(f"Unverified user {current_user.id} attempted to roll API key from {ip_address}")
            log_security_event(
                "UNVERIFIED_API_KEY_ROLL_ATTEMPT",
                {"user_id": current_user.id, "email": current_user.email, "ip_address": ip_address},
                severity="WARNING"
            )
            raise VerificationError('Please verify your account first')

        if not current_user.merchant_info:
            logger.warning(f"User {current_user.id} without merchant account attempted to roll API key")
            raise MerchantAccountNotFoundError("Please create a merchant account first")

        new_key, raw_key = MerchantService.roll_api_key(db=db, user_id=current_user.id, key_id=key_id)

        log_security_event(
            event_type="API_KEY_ROLLED",
            details={
                "user_id": current_user.id,
                "old_key_id": key_id,
                "new_key_id": new_key.id,
                "merchant_id": current_user.merchant_info.merchant_id,
                "ip_address": ip_address
            },
            severity="INFO"
        )

        log_user_action(
            db=db,
            user_id=current_user.id,
            action="API_KEY_ROLLED",
            resource_type="API_KEY",
            resource_id=str(new_key.id),
            merchant_id=current_user.merchant_info.merchant_id,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            extra_data={
                "old_key_id": key_id,
                "new_key_id": new_key.id,
                "rolled_at": datetime.now(timezone.utc).isoformat()
            }
        )
        db.commit()

        logger.info(f"User {current_user.id} rolled API key {key_id} to {new_key.id}")

        return api_key_schema.APIKeyFullRes(
            id=new_key.id,
            merchant_id=new_key.merchant_id,
            name=new_key.name,
            key_type=new_key.key_type,
            environment=new_key.environment,
            key_prefix=new_key.key_prefix,
            is_active=new_key.is_active,
            created_at=new_key.created_at,
            last_used_at=new_key.last_used_at,
            api_key=raw_key
        )

    except VerificationError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except (MerchantAccountNotFoundError, ResourceNotFoundError) as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except DatabaseError as e:
        db.rollback()
        logger.error(f"Database error rolling API key {key_id} for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to roll API key")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error rolling API key {key_id} for user {current_user.id}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred")

