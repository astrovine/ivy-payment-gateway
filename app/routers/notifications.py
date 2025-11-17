from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..utilities.db_con import get_db
from ..utilities import Oauth2 as au
from ..models import db_models
from ..services.notification_service import NotificationService
from typing import List
from ..schemas import admin as admin_schemas

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])

@router.get("/", response_model=List[admin_schemas.NotificationResponse])
async def list_notifications(skip: int = 0, limit: int = 50, db: Session = Depends(get_db), current_user: db_models.User = Depends(au.get_current_user_or_api_key)):
    merchant_id = current_user.merchant_info.merchant_id if hasattr(current_user, 'merchant_info') and current_user.merchant_info else None
    if not merchant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No merchant account")
    notes = NotificationService.list_notifications(db=db, merchant_id=merchant_id, limit=limit, skip=skip)
    return notes

@router.get('/unread_count')
async def unread_count(db: Session = Depends(get_db), current_user: db_models.User = Depends(au.get_current_user_or_api_key)):
    merchant_id = current_user.merchant_info.merchant_id if hasattr(current_user, 'merchant_info') and current_user.merchant_info else None
    if not merchant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No merchant account")
    count = NotificationService.get_unread_count(db=db, merchant_id=merchant_id)
    return {"unread": count}

@router.put('/{notification_id}/read')
async def mark_read(notification_id: int, db: Session = Depends(get_db), current_user: db_models.User = Depends(au.get_current_user_or_api_key)):
    merchant_id = current_user.merchant_info.merchant_id if hasattr(current_user, 'merchant_info') and current_user.merchant_info else None
    if not merchant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No merchant account")
    n = NotificationService.mark_read(db=db, merchant_id=merchant_id, notification_id=notification_id)
    return n

@router.put('/read_all')
async def mark_all_read(db: Session = Depends(get_db), current_user: db_models.User = Depends(au.get_current_user_or_api_key)):
    merchant_id = current_user.merchant_info.merchant_id if hasattr(current_user, 'merchant_info') and current_user.merchant_info else None
    if not merchant_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No merchant account")
    NotificationService.mark_all_read(db=db, merchant_id=merchant_id)
    return {"message": "ok"}
