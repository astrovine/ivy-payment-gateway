from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import List

from ..schemas import webhook as webhook_schema
from ..services.webhook_service import WebhookService
from ..utilities.db_con import get_db
from ..utilities import Oauth2 as au
from ..models import db_models
from ..utilities.logger import setup_logger, log_user_action

router = APIRouter(prefix="/api/v1/webhooks", tags=["Webhooks"])
logger = setup_logger(__name__)


@router.post("/", response_model=webhook_schema.WebhookRes, status_code=status.HTTP_201_CREATED)
async def create_webhook(
    payload: webhook_schema.WebhookCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user)
):
    logger.info(f"Creating webhook for user {current_user.email} from {request.client.host}")
    wh = WebhookService.create_webhook(db=db, merchant_id=current_user.merchant_info.merchant_id, data=payload.dict())
    log_user_action(db=db, user_id=current_user.id, action="WEBHOOK_CREATED", resource_type="WEBHOOK", resource_id=str(wh.id), merchant_id=current_user.merchant_info.merchant_id, ip_address=request.client.host if request.client else None, user_agent=request.headers.get('user-agent'))
    return wh


@router.get("/", response_model=List[webhook_schema.WebhookRes])
async def list_webhooks(
    db: Session = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user)
):
    return WebhookService.list_webhooks(db=db, merchant_id=current_user.merchant_info.merchant_id)


@router.get("/{webhook_id}", response_model=webhook_schema.WebhookRes)
async def get_webhook(webhook_id: int, db: Session = Depends(get_db), current_user: db_models.User = Depends(au.get_current_user)):
    wh = WebhookService.get_webhook(db=db, merchant_id=current_user.merchant_info.merchant_id, webhook_id=webhook_id)
    return wh


@router.put("/{webhook_id}", response_model=webhook_schema.WebhookRes)
async def update_webhook(webhook_id: int, payload: webhook_schema.WebhookUpdate, db: Session = Depends(get_db), current_user: db_models.User = Depends(au.get_current_user), request: Request = None):
    wh = WebhookService.update_webhook(db=db, merchant_id=current_user.merchant_info.merchant_id, webhook_id=webhook_id, data=payload.dict(exclude_unset=True))
    log_user_action(db=db, user_id=current_user.id, action="WEBHOOK_UPDATED", resource_type="WEBHOOK", resource_id=str(wh.id), merchant_id=current_user.merchant_info.merchant_id, ip_address=request.client.host if request and request.client else None, user_agent=request.headers.get('user-agent') if request else None)
    return wh


@router.delete("/{webhook_id}")
async def delete_webhook(webhook_id: int, db: Session = Depends(get_db), current_user: db_models.User = Depends(au.get_current_user), request: Request = None):
    WebhookService.delete_webhook(db=db, merchant_id=current_user.merchant_info.merchant_id, webhook_id=webhook_id)
    log_user_action(db=db, user_id=current_user.id, action="WEBHOOK_DELETED", resource_type="WEBHOOK", resource_id=str(webhook_id), merchant_id=current_user.merchant_info.merchant_id, ip_address=request.client.host if request and request.client else None, user_agent=request.headers.get('user-agent') if request else None)
    return {"ok": True}


@router.post("/{webhook_id}/test")
async def test_webhook(webhook_id: int, db: Session = Depends(get_db), current_user: db_models.User = Depends(au.get_current_user)):
    wh = WebhookService.get_webhook(db=db, merchant_id=current_user.merchant_info.merchant_id, webhook_id=webhook_id)
    payload = {"event": "webhook.test", "merchant_id": current_user.merchant_info.merchant_id}
    delivery = WebhookService.record_delivery(db=db, webhook_id=wh.id, event="webhook.test", payload=payload)
    from app.celery_worker import celery_app
    celery_app.send_task("app.tasks.process_webhook_delivery", args=(delivery.id,))
    return {"ok": True, "delivery_id": delivery.id}


@router.get("/{webhook_id}/deliveries", response_model=List[webhook_schema.WebhookDeliveryRes])
async def list_deliveries(webhook_id: int, db: Session = Depends(get_db), current_user: db_models.User = Depends(au.get_current_user)):
    _ = WebhookService.get_webhook(db=db, merchant_id=current_user.merchant_info.merchant_id, webhook_id=webhook_id)
    return WebhookService.list_deliveries(db=db, webhook_id=webhook_id)


@router.post("/{webhook_id}/deliveries/{delivery_id}/retry")
async def retry_delivery(webhook_id: int, delivery_id: int, db: Session = Depends(get_db), current_user: db_models.User = Depends(au.get_current_user)):
    _ = WebhookService.get_delivery(db=db, webhook_id=webhook_id, delivery_id=delivery_id)
    from app.celery_worker import celery_app
    celery_app.send_task("app.tasks.process_webhook_delivery", args=(delivery_id,))
    return {"ok": True}

