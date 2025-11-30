import secrets
import uuid
from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
import hashlib
import hmac

from fastapi import HTTPException
from pydantic import EmailStr
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import select

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
    def create_user(db: Session, user_data: user_schema.UserCreate) -> db_models.User:
        """
        Create a new user account

        Args:
            db: Database session
            user_data: User creation data

        Returns:
            Created User object

        Raises:
            DuplicateEmailError: If email already exists
            UserCreationError: If creation fails for other reasons
        """
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
            db.flush()
            db.refresh(new_user)

            logger.info(f"User created successfully: {new_user.id} ({new_user.email})")
            return new_user

        except IntegrityError as e:
            db.rollback()
            logger.warning(f"Integrity error while creating user {user_data.email}: {str(e)}")
            if "email" in str(e).lower():
                raise DuplicateEmailError()
            raise UserCreationError("Email already exists or constraint violated")
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error creating user {user_data.email}:  {str(e)}", exc_info=True)
            raise UserCreationError(str(e))

    @staticmethod
    def find_or_create_by_oauth(db: Session, user_info: dict) -> db_models.User:
        """
        Finds a user by email from OAuth info. If they don't exist,
        create them.
        """
        email = user_info.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Email not provided by OAuth provider")

        user = db.query(db_models.User).filter_by(email=email).first()

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
            db.commit()
            db.refresh(new_user)
            return new_user
        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create OAuth user: {e}", exc_info=True)
            raise HTTPException(status_code=500, detail="Could not create user account.")

    @staticmethod
    def verify_user_account(
        db: Session,
        current_user: db_models.User,
        verification_data: user_schema.UserVer
    ) -> db_models.UserVerified:
        """
        Verify a user account with business details

        Args:
            db: Database session
            current_user: The authenticated user
            verification_data: Business verification data

        Returns:
            Created UserVerified object

        Raises:
            UserAlreadyVerifiedError: If user is already verified
            VerificationError: If verification fails
        """
        try:
            logger.info(f"Verifying user account: {current_user.id} ({current_user.email})")
            existing = db.query(db_models.UserVerified).filter(
                db_models.UserVerified.user_id == current_user.id
            ).first()

            if existing:
                logger.warning(f"User {current_user.id} is already verified")
                raise UserAlreadyVerifiedError()
            website_str = str(verification_data.business_website) if verification_data.business_website else None
            ver_data = verification_data.model_dump()
            ver_data["user_id"] = current_user.id
            ver_data['business_website'] = website_str

            new_verification = db_models.UserVerified(**ver_data)
            db.add(new_verification)
            db.flush()
            db.refresh(new_verification)

            logger.info(f"User {current_user.id} verified successfully as {verification_data.business_name}")
            return new_verification

        except UserAlreadyVerifiedError:
            raise
        except IntegrityError as e:
            db.rollback()
            logger.error(f"Integrity error verifying user {current_user.id}: {str(e)}")
            raise VerificationError("Business email may already be in use")
        except Exception as e:
            db.rollback()
            logger.error(f"Unexpected error verifying user {current_user.id}: {str(e)}", exc_info=True)
            raise VerificationError(str(e))

    @staticmethod
    def update_user_account(db: Session, user_id: int, update_data: user_schema.UserUpdate) -> db_models.User:
        """
        Update an existing user account.

        Args:
            db: Database session
            user_id: ID of the user to update
            update_data: Pydantic model with fields to update

        Returns:
            The updated User object

        Raises:
            UserNotFoundError: If the user doesn't exist
        """
        user_query = db.query(db_models.User).filter(db_models.User.id == user_id)
        db_user = user_query.first()

        if not db_user:
            raise UserNotFoundError(f"User with id {user_id} not found")

        try:
            update_dict = update_data.model_dump(exclude_unset=True)
            user_query.update(update_dict, synchronize_session=False)
            db.flush()
            db.refresh(db_user)
            updated_user = user_query.first()

            logger.info(f"User {user_id} updated successfully.")
            return updated_user

        except Exception as e:
            db.rollback()
            logger.error(f"Error updating user {user_id}: {str(e)}", exc_info=True)
            raise Exception("Unexpected error updating user")

    @staticmethod
    def change_user_password(
            db: Session,
            user: db_models.User,
            old_password: str,
            new_password: str,
            confirm_password: str
    ) -> None:
        """Changes the password for a given user."""
        if not verify_password(old_password, user.password):
            raise InvalidCredentialsError("Old password is incorrect")

        if new_password != confirm_password:
            raise PasswordMismatchError("New passwords do not match")
        try:
            hashed_new_password = hash_password(new_password)
            user.password = hashed_new_password
            db.flush()
            db.refresh(user)
            logger.debug(f"Password updated in DB for user {user.id}")
        except Exception as e:
            db.rollback()
            logger.error(f"Database error updating password for user {user.id}: {e}", exc_info=True)
            raise DatabaseError("Failed to update password")

        return

    @staticmethod
    def request_password_reset(db: Session, email: EmailStr) -> tuple[str, db_models.User] | None:
        """
        Generate password reset token for user.

        Args:
            db: Database session
            email: User's email address

        Returns:
            Tuple of (reset_token, user) if user exists, None otherwise

        Note:
            Returns None silently if user doesn't exist (security best practice)
            The raw token should be sent via email, never stored
        """
        try:
            user = db.query(db_models.User).filter(db_models.User.email == email).first()
            if not user:
                logger.info(f"Password reset requested for non-existent email: {email}")
                return None

            raw_token = secrets.token_urlsafe(32)

            # Store deterministic SHA-256 hash of token (never store raw token)
            hashed_token = hashlib.sha256(raw_token.encode()).hexdigest()

            expiration = datetime.now(timezone.utc) + timedelta(minutes=15)

            user.password_reset_token = hashed_token
            user.password_reset_expires = expiration

            # Ensure persistence for subsequent queries in the same test/request
            db.commit()
            db.refresh(user)

            logger.info(f"Password reset token generated for user {user.id} ({user.email}), expires at {expiration}")

            return (raw_token, user)

        except Exception as e:
            db.rollback()
            logger.error(f"Error generating password reset token for {email}: {str(e)}", exc_info=True)
            raise DatabaseError("Failed to generate password reset token")

    @staticmethod
    def verify_reset_token(db: Session, token: str) -> db_models.User:
        """
        Verify password reset token and return user.

        Args:
            db: Database session
            token: Raw reset token from email link

        Returns:
            User object if token is valid

        Raises:
            InvalidResetTokenError: If token is invalid
            ExpiredResetTokenError: If token has expired
        """
        try:
            provided_digest = hashlib.sha256(token.encode()).hexdigest()

            user = db.query(db_models.User).filter(
                db_models.User.password_reset_token == provided_digest
            ).first()

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
    def reset_password(db: Session, token: str, new_password: str, confirm_password: str) -> None:
        """
        Reset user password using valid reset token.

        Args:
            db: Database session
            token: Raw reset token from email link
            new_password: New password
            confirm_password: Confirmation of new password

        Raises:
            PasswordMismatchError: If passwords don't match
            InvalidResetTokenError: If token is invalid
            ExpiredResetTokenError: If token has expired
        """
        # Validate passwords match
        if new_password != confirm_password:
            raise PasswordMismatchError("New passwords do not match")

        try:
            user = UserService.verify_reset_token(db, token)

            hashed_password = hash_password(new_password)

            user.password = hashed_password
            user.password_reset_token = None
            user.password_reset_expires = None

            db.commit()
            db.refresh(user)

            logger.info(f"Password successfully reset for user {user.id} ({user.email})")

        except (PasswordMismatchError, InvalidResetTokenError, ExpiredResetTokenError):
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Error resetting password: {str(e)}", exc_info=True)
            raise DatabaseError()

    @staticmethod
    def delete_user_account(db: Session, user_id: int) -> db_models.User:
        """
        Delete an existing user account.
        :param db:
        :param user_id:
        :return:
        """
        return (
            db.query(db_models.User).filter(db_models.User.id == user_id).delete(synchronize_session=False)
        )

    @staticmethod
    def get_full_user_info(db: Session, user_id: int) -> db_models.User | None:
        """
        Get full user info including verification details if available.

        Args:
            db: Database session
            user_id: ID of the user to retrieve

        Returns:
            User object with eagerly loaded verified_info (can be None if not verified)
            Returns None if user doesn't exist

        Note:
            User.verified_info will be None if user hasn't verified their account yet
        """
        user = (
            db.query(db_models.User)
            .options(joinedload(db_models.User.verified_info))
            .filter(db_models.User.id == user_id)
            .first()
        )

        if user:
            logger.debug(f"Retrieved user {user_id}, verified_info present: {user.verified_info is not None}")
        else:
            logger.warning(f"User {user_id} not found")

        return user

    @staticmethod
    def get_activity_logs(db: Session, user: db_models.User ) -> Sequence[db_models.AuditLog]:
        try:
            cur = select(db_models.AuditLog)
            cur = cur.where(db_models.AuditLog.user_id == user.id).order_by(db_models.AuditLog.created_at.desc())
            if user.merchant_info and user.merchant_info.merchant_id:
                cur = cur.where(db_models.AuditLog.merchant_id == user.merchant_info.merchant_id).order_by(db_models.AuditLog.created_at.desc())
            result = db.execute(cur)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting activity logs: {str(e)}", exc_info=True)
            raise DatabaseError()

    @staticmethod
    def get_user_by_id(db: Session, user_id: int) -> db_models.User:
        return db.query(db_models.User).filter(db_models.User.id == user_id).first()

    @staticmethod
    def get_user_by_email(db: Session, email: str) -> db_models.User:
        return db.query(db_models.User).filter(db_models.User.email == email).first()
