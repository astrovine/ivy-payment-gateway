from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import db_models
from app.utilities.logger import setup_logger
from app.utilities.exceptions import ResourceNotFoundError
from datetime import datetime, timezone
import json

logger = setup_logger(__name__)


class WebhookService:
    @staticmethod
    async def create_webhook(db: AsyncSession, merchant_id: str, data: dict) -> db_models.WebhookEndpoint:
        secret = data.get('secret')
        encrypted_secret = None
        if secret:
            from app.utilities.encryption import encrypt_value
            encrypted_secret = encrypt_value(secret)
        
        webhook = db_models.WebhookEndpoint(
            merchant_id=merchant_id,
            url=data.get('url'),
            description=data.get('description'),
            events=data.get('events'),
            secret=encrypted_secret,
            enabled=data.get('enabled', True),
            api_version=data.get('api_version')
        )
        db.add(webhook)
        await db.commit()
        await db.refresh(webhook)
        logger.info(f"Created webhook {webhook.id} for merchant {merchant_id}")
        return webhook

    @staticmethod
    async def list_webhooks(db: AsyncSession, merchant_id: str):
        result = await db.execute(select(db_models.WebhookEndpoint).where(db_models.WebhookEndpoint.merchant_id == merchant_id))
        return result.scalars().all()

    @staticmethod
    async def get_webhook(db: AsyncSession, merchant_id: str, webhook_id: int):
        result = await db.execute(
            select(db_models.WebhookEndpoint)
            .where(db_models.WebhookEndpoint.id == webhook_id, db_models.WebhookEndpoint.merchant_id == merchant_id)
        )
        wh = result.scalar_one_or_none()
        if not wh:
            raise ResourceNotFoundError('Webhook endpoint')
        return wh

    @staticmethod
    async def update_webhook(db: AsyncSession, merchant_id: str, webhook_id: int, data: dict):
        wh = await WebhookService.get_webhook(db, merchant_id, webhook_id)
        for k, v in data.items():
            if v is not None and hasattr(wh, k):
                setattr(wh, k, v)
        wh.updated_at = datetime.now(timezone.utc)
        db.add(wh)
        await db.commit()
        await db.refresh(wh)
        return wh

    @staticmethod
    async def delete_webhook(db: AsyncSession, merchant_id: str, webhook_id: int):
        wh = await WebhookService.get_webhook(db, merchant_id, webhook_id)
        await db.delete(wh)
        await db.commit()
        return True

    @staticmethod
    async def record_delivery(db: AsyncSession, webhook_id: int, event: str, payload: str, status: str = 'pending', http_status: int = None, response_body: str = None):
        try:
            if isinstance(payload, (dict, list)):
                payload_str = json.dumps(payload)
            else:
                try:
                    parsed = json.loads(payload)
                    payload_str = json.dumps(parsed)
                except Exception:
                    payload_str = str(payload)
        except Exception:
            payload_str = str(payload)

        d = db_models.WebhookDelivery(
            webhook_id=webhook_id,
            event=event,
            payload=payload_str,
            status=status or 'pending',
            http_status=http_status,
            response_body=response_body,
            attempts=0
        )
        db.add(d)
        await db.commit()
        await db.refresh(d)
        return d

    @staticmethod
    async def list_deliveries(db: AsyncSession, webhook_id: int):
        result = await db.execute(
            select(db_models.WebhookDelivery)
            .where(db_models.WebhookDelivery.webhook_id == webhook_id)
            .order_by(db_models.WebhookDelivery.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def get_delivery(db: AsyncSession, webhook_id: int, delivery_id: int):
        result = await db.execute(
            select(db_models.WebhookDelivery)
            .where(db_models.WebhookDelivery.webhook_id == webhook_id, db_models.WebhookDelivery.id == delivery_id)
        )
        d = result.scalar_one_or_none()
        if not d:
            raise ResourceNotFoundError('Delivery')
        return d

    @staticmethod
    async def increment_and_update_delivery(db: AsyncSession, delivery: db_models.WebhookDelivery, status: str, http_status: int = None, response_body: str = None):
        delivery.attempts = (delivery.attempts or 0) + 1
        delivery.status = status
        delivery.http_status = http_status
        delivery.response_body = response_body
        delivery.last_attempt_at = datetime.now(timezone.utc)
        db.add(delivery)
        await db.commit()
        await db.refresh(delivery)
        return delivery
