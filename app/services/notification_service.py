from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import db_models
from app.utilities.logger import setup_logger
from app.utilities.exceptions import ResourceNotFoundError
from datetime import datetime, timezone

logger = setup_logger(__name__)


class NotificationService:
    @staticmethod
    async def list_notifications(db: AsyncSession, merchant_id: str, limit: int = 50, skip: int = 0):
        result = await db.execute(
            select(db_models.Notification)
            .where(db_models.Notification.merchant_id == merchant_id)
            .order_by(db_models.Notification.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def get_unread_count(db: AsyncSession, merchant_id: str):
        result = await db.execute(
            select(func.count(db_models.Notification.id))
            .where(db_models.Notification.merchant_id == merchant_id, db_models.Notification.is_read == False)
        )
        return result.scalar() or 0

    @staticmethod
    async def mark_read(db: AsyncSession, merchant_id: str, notification_id: int):
        result = await db.execute(
            select(db_models.Notification)
            .where(db_models.Notification.merchant_id == merchant_id, db_models.Notification.id == notification_id)
        )
        n = result.scalar_one_or_none()
        if not n:
            raise ResourceNotFoundError('Notification')
        n.is_read = True
        n.updated_at = datetime.now(timezone.utc)
        db.add(n)
        await db.commit()
        await db.refresh(n)
        return n

    @staticmethod
    async def mark_all_read(db: AsyncSession, merchant_id: str):
        await db.execute(
            update(db_models.Notification)
            .where(db_models.Notification.merchant_id == merchant_id, db_models.Notification.is_read == False)
            .values(is_read=True)
        )
        await db.commit()
        return True

    @staticmethod
    async def create_notification(db: AsyncSession, merchant_id: str, user_id: int | None, type: str, message: str, data: str | None = None) -> db_models.Notification:
        n = db_models.Notification(
            merchant_id=merchant_id,
            user_id=user_id,
            type=type,
            message=message,
            data=data,
            is_read=False
        )
        db.add(n)
        await db.commit()
        await db.refresh(n)
        logger.info(f"Notification created for merchant {merchant_id}: {type} - {message}")
        return n
