from sqlalchemy.orm import Session
from app.models import db_models
from app.utilities.logger import setup_logger
from app.utilities.exceptions import ResourceNotFoundError
from datetime import datetime, timezone
import json

logger = setup_logger(__name__)

class WebhookService:
    @staticmethod
    def create_webhook(db: Session, merchant_id: str, data: dict) -> db_models.WebhookEndpoint:
        webhook = db_models.WebhookEndpoint(
            merchant_id=merchant_id,
            url=data.get('url'),
            description=data.get('description'),
            events=data.get('events'),
            secret=data.get('secret'),
            enabled=data.get('enabled', True),
            api_version=data.get('api_version')
        )
        db.add(webhook)
        db.commit()
        db.refresh(webhook)
        logger.info(f"Created webhook {webhook.id} for merchant {merchant_id}")
        return webhook

    @staticmethod
    def list_webhooks(db: Session, merchant_id: str):
        return db.query(db_models.WebhookEndpoint).filter_by(merchant_id=merchant_id).all()

    @staticmethod
    def get_webhook(db: Session, merchant_id: str, webhook_id: int):
        wh = db.query(db_models.WebhookEndpoint).filter_by(id=webhook_id, merchant_id=merchant_id).first()
        if not wh:
            raise ResourceNotFoundError('Webhook endpoint')
        return wh

    @staticmethod
    def update_webhook(db: Session, merchant_id: str, webhook_id: int, data: dict):
        wh = WebhookService.get_webhook(db, merchant_id, webhook_id)
        for k, v in data.items():
            if v is not None and hasattr(wh, k):
                setattr(wh, k, v)
        wh.updated_at = datetime.now(timezone.utc)
        db.add(wh)
        db.commit()
        db.refresh(wh)
        return wh

    @staticmethod
    def delete_webhook(db: Session, merchant_id: str, webhook_id: int):
        wh = WebhookService.get_webhook(db, merchant_id, webhook_id)
        db.delete(wh)
        db.commit()
        return True

    @staticmethod
    def record_delivery(db: Session, webhook_id: int, event: str, payload: str, status: str = 'pending', http_status: int = None, response_body: str = None):
        """Create a webhook delivery record. Payload can be dict or string; it will be stored as JSON string."""
        # ensure payload stored as JSON string
        try:
            if isinstance(payload, (dict, list)):
                payload_str = json.dumps(payload)
            else:
                # try to load then dump to normalize, else keep as string
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
        db.commit()
        db.refresh(d)
        return d

    @staticmethod
    def list_deliveries(db: Session, webhook_id: int):
        # order by created_at descending
        return db.query(db_models.WebhookDelivery).filter_by(webhook_id=webhook_id).order_by(db_models.WebhookDelivery.created_at.desc()).all()

    @staticmethod
    def get_delivery(db: Session, webhook_id: int, delivery_id: int):
        d = db.query(db_models.WebhookDelivery).filter_by(webhook_id=webhook_id, id=delivery_id).first()
        if not d:
            raise ResourceNotFoundError('Delivery')
        return d

    @staticmethod
    def increment_and_update_delivery(db: Session, delivery: db_models.WebhookDelivery, status: str, http_status: int = None, response_body: str = None):
        delivery.attempts = (delivery.attempts or 0) + 1
        delivery.status = status
        delivery.http_status = http_status
        delivery.response_body = response_body
        delivery.last_attempt_at = datetime.now(timezone.utc)
        db.add(delivery)
        db.commit()
        db.refresh(delivery)
        return delivery
