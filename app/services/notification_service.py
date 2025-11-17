from sqlalchemy.orm import Session
from app.models import db_models
from app.utilities.logger import setup_logger
from app.utilities.exceptions import ResourceNotFoundError
from datetime import datetime, timezone

logger = setup_logger(__name__)

class NotificationService:
    @staticmethod
    def list_notifications(db: Session, merchant_id: str, limit: int = 50, skip: int = 0):
        return db.query(db_models.Notification).filter_by(merchant_id=merchant_id).order_by(db_models.Notification.created_at.desc()).offset(skip).limit(limit).all()

    @staticmethod
    def get_unread_count(db: Session, merchant_id: str):
        return db.query(db_models.Notification).filter_by(merchant_id=merchant_id, is_read=False).count()

    @staticmethod
    def mark_read(db: Session, merchant_id: str, notification_id: int):
        n = db.query(db_models.Notification).filter_by(merchant_id=merchant_id, id=notification_id).first()
        if not n:
            raise ResourceNotFoundError('Notification')
        n.is_read = True
        n.updated_at = datetime.now(timezone.utc)
        db.add(n)
        db.commit()
        db.refresh(n)
        return n

    @staticmethod
    def mark_all_read(db: Session, merchant_id: str):
        db.query(db_models.Notification).filter_by(merchant_id=merchant_id, is_read=False).update({'is_read': True})
        db.commit()
        return True

    @staticmethod
    def create_notification(db: Session, merchant_id: str, user_id: int | None, type: str, message: str, data: str | None = None) -> db_models.Notification:
        n = db_models.Notification(
            merchant_id=merchant_id,
            user_id=user_id,
            type=type,
            message=message,
            data=data,
            is_read=False
        )
        db.add(n)
        db.commit()
        db.refresh(n)
        logger.info(f"Notification created for merchant {merchant_id}: {type} - {message}")
        return n
