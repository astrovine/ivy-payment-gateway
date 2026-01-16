import secrets
import uuid
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
import hashlib

from fastapi import HTTPException
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload
from sqlalchemy import select, delete, update

from ..models import db_models
from ..schemas import account as user_schema
from ..utilities.exceptions import (
    DuplicateEmailError,
    UserCreationError,
    UserAlreadyVerifiedError,
    VerificationError,
    UserNotFoundError,
    InvalidCredentialsError,
    PasswordMismatchError,
    DatabaseError,
    InvalidResetTokenError,
    ExpiredResetTokenError,
)
from ..utilities.logger import setup_logger
from ..utilities.utils import hash_password, verify_password

logger = setup_logger("payment_gateway.services.user_service")


class UserService:
    @staticmethod
    async def create_user(db: AsyncSession, user_data: user_schema.UserCreate) -> db_models.User:
        try:
            logger.info(f"Creating user with email: {user_data.email}")
            hashed_password = hash_password(user_data.password)
            new_user = db_models.User(
                name=user_data.name,
                email=user_data.email,
                password=hashed_password,
                country=user_data.country,
                is_active=True
            )

            db.add(new_user)
            await db.flush()
            await db.refresh(new_user)

            logger.info(f"User created successfully: {new_user.id} ({new_user.email})")
            return new_user

        except IntegrityError as e:
            await db.rollback()
            logger.warning(f"Integrity error while creating user {user_data.email}: {str(e)}")
            if "email" in str(e).lower():
                raise DuplicateEmailError()
            raise UserCreationError("Email already exists or constraint violated")
        except Exception as e:
            await db.rollback()
            logger.error(f"Unexpected error creating user {user_data.email}:  {str(e)}", exc_info=True)
            raise UserCreationError(str(e))

    @staticmethod
    async def find_or_create_by_oauth(db: AsyncSession, user_info: dict) -> db_models.User:
        email = user_info.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Email not provided by OAuth provider")

        result = await db.execute(select(db_models.User).where(db_models.User.email == email))
        user = result.scalar_one_or_none()

        if user:
            return user

        random_password = str(uuid.uuid4())
        hashed_password = hash_password(random_password)

        new_user = db_models.User(
            name=user_info.get("name", "New User"),
            email=email,
            password=hashed_password,
            country=user_info.get("locale", "US"),
            is_active=True
        )

        db.add(new_user)

        try:
            await db.commit()
            await db.refresh(new_user)
            return new_user
        except Exception as e:
            await db.rollback()
            logger.error(f"Failed to create OAuth user: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Could not create user account.")

    @staticmethod
    async def verify_user_account(
        db: AsyncSession,
        current_user: db_models.User,
        verification_data: user_schema.UserVer
    ) -> db_models.UserVerified:
        try:
            logger.info(f"Verifying user account: {current_user.id} ({current_user.email})")
            result = await db.execute(
                select(db_models.UserVerified).where(db_models.UserVerified.user_id == current_user.id)
            )
            existing = result.scalar_one_or_none()

            if existing:
                logger.warning(f"User {current_user.id} is already verified")
                raise UserAlreadyVerifiedError()

            website_str = str(verification_data.business_website) if verification_data.business_website else None
            ver_data = verification_data.model_dump()
            ver_data["user_id"] = current_user.id
            ver_data['business_website'] = website_str

            new_verification = db_models.UserVerified(**ver_data)
            db.add(new_verification)
            await db.flush()
            await db.refresh(new_verification)

            logger.info(f"User {current_user.id} verified successfully as {verification_data.business_name}")
            return new_verification

        except UserAlreadyVerifiedError:
            raise
        except IntegrityError as e:
            await db.rollback()
            logger.error(f"Integrity error verifying user {current_user.id}: {str(e)}")
            raise VerificationError("Business email may already be in use")
        except Exception as e:
            await db.rollback()
            logger.error(f"Unexpected error verifying user {current_user.id}: {str(e)}", exc_info=True)
            raise VerificationError(str(e))

    @staticmethod
    async def update_user_account(db: AsyncSession, user_id: int, update_data: user_schema.UserUpdate) -> db_models.User:
        result = await db.execute(select(db_models.User).where(db_models.User.id == user_id))
        db_user = result.scalar_one_or_none()

        if not db_user:
            raise UserNotFoundError(f"User with id {user_id} not found")

        try:
            update_dict = update_data.model_dump(exclude_unset=True)
            for key, value in update_dict.items():
                setattr(db_user, key, value)

            await db.flush()
            await db.refresh(db_user)

            logger.info(f"User {user_id} updated successfully.")
            return db_user

        except Exception as e:
            await db.rollback()
            logger.error(f"Error updating user {user_id}: {str(e)}", exc_info=True)
            raise Exception("Unexpected error updating user")

    @staticmethod
    async def change_user_password(
            db: AsyncSession,
            user: db_models.User,
            old_password: str,
            new_password: str,
            confirm_password: str
    ) -> None:
        if not verify_password(old_password, user.password):
            raise InvalidCredentialsError("Old password is incorrect")

        if new_password != confirm_password:
            raise PasswordMismatchError("New passwords do not match")
        try:
            hashed_new_password = hash_password(new_password)
            user.password = hashed_new_password
            await db.flush()
            await db.refresh(user)
            logger.debug(f"Password updated in DB for user {user.id}")
        except Exception as e:
            await db.rollback()
            logger.error(f"Database error updating password for user {user.id}: {e}", exc_info=True)
            raise DatabaseError("Failed to update password")

        return

    @staticmethod
    async def request_password_reset(db: AsyncSession, email: EmailStr) -> tuple[str, db_models.User] | None:
        try:
            result = await db.execute(select(db_models.User).where(db_models.User.email == email))
            user = result.scalar_one_or_none()
            if not user:
                logger.info(f"Password reset requested for non-existent email: {email}")
                return None

            raw_token = secrets.token_urlsafe(32)
            hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()
            expiration = datetime.now(timezone.utc) + timedelta(minutes=15)

            user.password_reset_token = hashed_token
            user.password_reset_expires = expiration

            await db.commit()
            await db.refresh(user)

            logger.info(f"Password reset token generated for user {user.id} ({user.email}), expires at {expiration}")

            return (raw_token, user)

        except Exception as e:
            await db.rollback()
            logger.error(f"Error generating password reset token for {email}: {str(e)}", exc_info=True)
            raise DatabaseError("Failed to generate password reset token")

    @staticmethod
    async def verify_reset_token(db: AsyncSession, token: str) -> db_models.User:
        try:
            provided_digest = hashlib.sha256(token.encode()).hexdigest()

            result = await db.execute(
                select(db_models.User).where(db_models.User.password_reset_token == provided_digest)
            )
            user = result.scalar_one_or_none()

            if not user:
                logger.warning("Invalid reset token attempted")
                raise InvalidResetTokenError()

            expires = user.password_reset_expires
            if expires is not None:
                if expires.tzinfo is None:
                    expires = expires.replace(tzinfo=timezone.utc)
                if expires < datetime.now(timezone.utc):
                    logger.warning(f"Expired reset token used for user {user.id}")
                    raise ExpiredResetTokenError()

            logger.info(f"Valid reset token verified for user {user.id}")
            return user

        except (ExpiredResetTokenError, InvalidResetTokenError):
            raise
        except Exception as e:
            logger.error(f"Error verifying reset token: {str(e)}", exc_info=True)
            raise InvalidResetTokenError()

    @staticmethod
    async def reset_password(db: AsyncSession, token: str, new_password: str, confirm_password: str) -> None:
        if new_password != confirm_password:
            raise PasswordMismatchError("New passwords do not match")

        try:
            user = await UserService.verify_reset_token(db, token)

            hashed_password = hash_password(new_password)

            user.password = hashed_password
            user.password_reset_token = None
            user.password_reset_expires = None

            await db.commit()
            await db.refresh(user)

            logger.info(f"Password successfully reset for user {user.id} ({user.email})")

        except (PasswordMismatchError, InvalidResetTokenError, ExpiredResetTokenError):
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Error resetting password: {str(e)}", exc_info=True)
            raise DatabaseError()

    @staticmethod
    async def delete_user_account(db: AsyncSession, user_id: int) -> int:
        result = await db.execute(delete(db_models.User).where(db_models.User.id == user_id))
        return result.rowcount

    @staticmethod
    async def get_full_user_info(db: AsyncSession, user_id: int) -> db_models.User | None:
        result = await db.execute(
            select(db_models.User)
            .options(joinedload(db_models.User.verified_info))
            .where(db_models.User.id == user_id)
        )
        user = result.unique().scalar_one_or_none()

        if user:
            logger.debug(f"Retrieved user {user_id}, verified_info present: {user.verified_info is not None}")
        else:
            logger.warning(f"User {user_id} not found")

        return user

    @staticmethod
    async def get_activity_logs(db: AsyncSession, user: db_models.User) -> Sequence[db_models.AuditLog]:
        try:
            stmt = select(db_models.AuditLog).where(db_models.AuditLog.user_id == user.id)
            if user.merchant_info and user.merchant_info.merchant_id:
                stmt = stmt.where(db_models.AuditLog.merchant_id == user.merchant_info.merchant_id)
            stmt = stmt.order_by(db_models.AuditLog.created_at.desc())
            result = await db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting activity logs: {str(e)}", exc_info=True)
            raise DatabaseError()

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: int) -> db_models.User | None:
        result = await db.execute(select(db_models.User).where(db_models.User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_user_by_email(db: AsyncSession, email: str) -> db_models.User | None:
        result = await db.execute(select(db_models.User).where(db_models.User.email == email))
        return result.scalar_one_or_none()
