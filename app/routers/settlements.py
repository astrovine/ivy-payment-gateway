from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from app.services.payout_service import PayoutService
from app.utilities.db_con import get_db
from app.utilities import Oauth2 as au
from app.models import db_models
from app.utilities.logger import setup_logger
from app.utilities.exceptions import MerchantAccountNotFoundError, DatabaseError
from app.schemas import payout as payout_schema

router = APIRouter(prefix="/api/v1/settlements", tags=["Settlements"])
logger = setup_logger(__name__)


@router.get("/", response_model=List[payout_schema.SettlementReportRes])
async def list_settlements(request: Request, db: Session = Depends(get_db), current_user: db_models.User = Depends(au.get_current_user)):
    try:
        reports = PayoutService.list_settlement_reports(db=db, user_id=current_user.id)
        return reports
    except MerchantAccountNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant account not found")
    except Exception as e:
        logger.exception("Error listing settlement reports")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/schedule")
async def get_schedule(request: Request, db: Session = Depends(get_db), current_user: db_models.User = Depends(au.get_current_user)):
    try:
        schedule = PayoutService.get_settlement_schedule(db=db, user_id=current_user.id)
        return schedule
    except MerchantAccountNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant account not found")
    except Exception as e:
        logger.exception("Error getting settlement schedule")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.put("/schedule")
async def update_schedule(data: payout_schema.SettlementScheduleUpdate, request: Request, db: Session = Depends(get_db), current_user: db_models.User = Depends(au.get_current_user)):
    try:
        updated = PayoutService.update_settlement_schedule(db=db, user_id=current_user.id, schedule=data.model_dump())
        return updated
    except MerchantAccountNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant account not found")
    except Exception as e:
        logger.exception("Error updating settlement schedule")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.get("/{payout_id}", response_model=payout_schema.SettlementReportRes)
async def get_settlement(payout_id: int, request: Request, db: Session = Depends(get_db), current_user: db_models.User = Depends(au.get_current_user)):
    try:
        report = PayoutService.get_settlement_report(db=db, user_id=current_user.id, payout_id=payout_id)
        return report
    except MerchantAccountNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Merchant account not found")
    except Exception as e:
        logger.exception(f"Error fetching settlement report {payout_id}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
