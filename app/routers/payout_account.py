from typing import List

from fastapi import APIRouter, Depends, status, HTTPException, Request
from sqlalchemy.orm import Session
from app.utilities.db_con import get_db
from app.utilities import exceptions
from app.models import db_models as dm, db_models
from app.schemas import payout
from ..utilities.Oauth2 import get_current_user
from ..utilities.logger import log_user_action, setup_logger
from datetime import datetime, timezone
from app.services.payout_service import PayoutAccountService as pa

router = APIRouter(prefix="/api/v1/payout-accounts", tags=["Payout Accounts"])
logger = setup_logger(__name__)

@router.post('/', status_code=status.HTTP_201_CREATED, response_model=payout.PayoutAccountRes)
async def create_payout_account(
    request: Request,
    data: payout.PayoutAccountCreate,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user)
):
    ip_address = request.client.host if request.client else ""
    logger.info(f"Processing payout creation request: {ip_address} by {current_user.email}")
    try:
        new_account = pa.create_payout_account(db=db, account=data, user=current_user)
        log_user_action(db, current_user.id, "create_payout_account", f"Created account {new_account.id}", ip_address)
        return new_account
    except exceptions.MerchantAccountNotFoundError as e:
        logger.warning(f"Failed payout account creation for {current_user.email}: {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except exceptions.PermissionDeniedError as e:
        logger.warning(f"Failed payout account creation for {current_user.email}: {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating payout account for {current_user.email}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred.")


@router.get('/', response_model=List[payout.PayoutAccountRes])
async def list_payout_accounts(
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user)
):
    logger.info(f"User {current_user.email} listing payout accounts.")
    try:
        accounts = pa.list_payout_accounts(db=db, user=current_user)
        return accounts
    except exceptions.MerchantAccountNotFoundError as e:
        logger.warning(f"Failed list payout accounts for {current_user.email}: {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Error listing payout accounts for {current_user.email}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred.")


@router.get('/{account_id}', response_model=payout.PayoutAccountRes)
async def get_payout_account(
    account_id: int,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user)
):
    logger.info(f"User {current_user.email} getting payout account {account_id}.")
    try:
        account = pa.get_payout_account(db=db, user=current_user, account_id=account_id)
        return account
    except exceptions.ServiceUnavailableError as e:
        logger.warning(f"Payout account {account_id} not found for user {current_user.email}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payout account not found.")
    except exceptions.PermissionDeniedError as e:
        logger.warning(f"Permission denied for user {current_user.email} on account {account_id}.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting payout account {account_id} for {current_user.email}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred.")


@router.put('/{account_id}', response_model=payout.PayoutAccountRes)
async def update_payout_account(
    account_id: int,
    data: payout.PayoutAccountUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user)
):
    ip_address = request.client.host if request.client else ""
    logger.info(f"User {current_user.email} updating payout account {account_id} from {ip_address}.")
    try:
        updated_account = pa.update_payout_account(
            db=db,
            user=current_user,
            account_id=account_id,
            account_update=data
        )
        log_user_action(db, current_user.id, "update_payout_account", f"Updated account {account_id}", ip_address)
        return updated_account
    except exceptions.ServiceUnavailableError as e:
        logger.warning(f"Payout account {account_id} not found for update by {current_user.email}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payout account not found.")
    except exceptions.PermissionDeniedError as e:
        logger.warning(f"Permission denied for user {current_user.email} on account {account_id}.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except exceptions.InvalidRequestError as e:
        logger.warning(f"Invalid request updating account {account_id} by {current_user.email}: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating payout account {account_id} for {current_user.email}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred.")


@router.delete('/{account_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_payout_account(
    account_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(get_current_user)
):
    ip_address = request.client.host if request.client else ""
    logger.info(f"User {current_user.email} deleting payout account {account_id} from {ip_address}.")
    try:
        pa.delete_payout_account(db=db, user=current_user, account_id=account_id)
        log_user_action(db, current_user.id, "delete_payout_account", f"Deleted account {account_id}", ip_address)
        return
    except exceptions.ServiceUnavailableError as e:
        logger.warning(f"Payout account {account_id} not found for deletion by {current_user.email}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payout account not found.")
    except exceptions.PermissionDeniedError as e:
        logger.warning(f"Failed delete attempt for account {account_id} by {current_user.email}: {e}")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting payout account {account_id} for {current_user.email}: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An internal error occurred.")