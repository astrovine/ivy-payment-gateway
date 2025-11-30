import secrets
from typing import List
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..models import db_models
from ..schemas import merchant as mer
from ..schemas import api_key as api_key_schema
from ..utilities.exceptions import (
    UserCreationError,
    DatabaseError,
    MerchantAccountNotFoundError,
    MerchantCreationError,
    ResourceNotFoundError,
)
from ..utilities.logger import setup_logger
from ..utilities.utils import hash_password

logger = setup_logger(__name__)

class MerchantService:
    @staticmethod
    def create_merchant_account(db: Session, data: mer.MerchantAccountCreate, user_id: int) -> db_models.MerchantAccount:
        try:
            logger.info("Creating a new merchant account")
            existing_account = db.query(db_models.MerchantAccount).filter_by(user_id=user_id).first()
            if existing_account:
                logger.warning(f'Merchant account {existing_account.id} already exists')
                raise DatabaseError('Merchant account already exists')
            mer_id = "merch_" + secrets.token_urlsafe(16)

            new_merchant = db_models.MerchantAccount(
                merchant_id=mer_id,
                user_id=user_id,
                currency=data.currency,
                settlement_schedule=data.settlement_schedule
            )
            db.add(new_merchant)
            db.commit()
            new_limit = db_models.TransactionLimit(
                merchant_id=mer_id
            )
            db.add(new_limit)
            db.commit()


            new_fee = db_models.FeeStructure(
                merchant_id=mer_id
            )
            db.add(new_fee)
            db.commit()

            new_settings = db_models.MerchantSettings(
                merchant_id=mer_id
            )
            db.add(new_settings)
            db.commit()
            pending_account = db_models.Account(
                merchant_id=mer_id,
                account_type=db_models.AccountType.MERCHANT_PENDING,
                currency=data.currency,
                balance=0
            )
            db.add(pending_account)
            db.commit()

            available_account = db_models.Account(
                merchant_id=mer_id,
                account_type=db_models.AccountType.MERCHANT_AVAILABLE,
                currency=data.currency,
                balance=0
            )
            db.add(available_account)
            db.commit()

            db.flush()
            db.refresh(new_merchant)
            logger.info(f'Merchant created successfully: {new_merchant.id}')
            return new_merchant

        except DatabaseError as e:
            db.rollback()
            logger.warning(f"Duplicate merchant check failed: {e}")
            raise e

        except IntegrityError as e:
            db.rollback()
            logger.error(f"IntegrityError: {e} while creating new merchant")
            raise UserCreationError(f"IntegrityError: {e} while creating new merchant")
        except Exception as e:
            db.rollback()
            logger.error(f"Exception: {e} while creating new merchant")
            raise MerchantCreationError(f"Exception: {e} while creating new merchant")


    @staticmethod
    def get_merchant_account(db: Session, user_id: int) -> db_models.MerchantAccount:
        try:
            logger.info(f"Getting a merchant account by mer_id: {user_id}")
            merchant = db.query(db_models.MerchantAccount).filter(db_models.MerchantAccount.user_id == user_id).first()
            if not merchant:
                logger.warning(f"Merchant account not found: {user_id}")
                raise MerchantAccountNotFoundError(reason='No merchant with that id was found')
            else:
                return merchant
        except Exception as e:
            logger.error(f"Exception: {e} while getting a merchant account")
            raise DatabaseError()

    @staticmethod
    def update_merchant_account(db: Session, user_id: int,
                                data: mer.MerchantAccountUpdate) -> db_models.MerchantAccount:

        try:
            logger.info(f"Merchant account update initiated for user_id: {user_id}")

            merchant_query = db.query(db_models.MerchantAccount).filter(db_models.MerchantAccount.user_id == user_id)
            db_merchant = merchant_query.first()

            if not db_merchant:
                logger.warning(f"Merchant account not found for user_id: {user_id}")
                raise MerchantAccountNotFoundError(reason='No merchant with that id was found')
            update_dict = data.model_dump(exclude_unset=True)
            if not update_dict:
                logger.info(f"No update data provided for user_id: {user_id}")
                return db_merchant
            merchant_query.update(update_dict, synchronize_session=False)
            db.flush()
            db.refresh(db_merchant)

            logger.info(f'Merchant account updated successfully for user_id: {user_id}')
            return db_merchant

        except MerchantAccountNotFoundError:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Exception: {e} while updating merchant account for user_id: {user_id}", exc_info=True)
            raise DatabaseError(f"Exception: {e} while updating a merchant account")


    @staticmethod
    def get_merchant_balance(db: Session, user_id: int) -> mer.MerchantBalanceRes:
        try:
            logger.info(f"Getting a merchant account balance for user_id: {user_id}")
            merchant = db.query(db_models.MerchantAccount).filter(db_models.MerchantAccount.user_id == user_id).first()
            if not merchant:
                logger.warning(f"Merchant account not found for user_id: {user_id}")
                raise MerchantAccountNotFoundError(reason='No merchant with that id was found')

            pending_sum = db.query(func.coalesce(func.sum(db_models.Account.balance), 0)).filter(
                db_models.Account.merchant_id == merchant.merchant_id,
                db_models.Account.account_type == db_models.AccountType.MERCHANT_PENDING
            ).scalar()

            available_sum = db.query(func.coalesce(func.sum(db_models.Account.balance), 0)).filter(
                db_models.Account.merchant_id == merchant.merchant_id,
                db_models.Account.account_type == db_models.AccountType.MERCHANT_AVAILABLE
            ).scalar()

            reserved_balance = merchant.reserved_balance if getattr(merchant, 'reserved_balance', None) is not None else Decimal("0.0000")

            logger.info(
                f"Balances for merchant {merchant.merchant_id}: pending={pending_sum}, available={available_sum}, reserved={reserved_balance}"
            )

            return mer.MerchantBalanceRes(
                available_balance=available_sum,
                pending_balance=pending_sum,
                reserved_balance=reserved_balance,
                currency=merchant.currency,
            )
        except MerchantAccountNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Exception: {e} while getting a merchant account balance")
            raise DatabaseError(f"Exception: {e} while getting a merchant account balance")

    @staticmethod
    def get_merchant_balance_history(db: Session, merchant_id: str) -> List[db_models.LedgerTransaction]:
        try:
            logger.info(f"Getting a merchant account balance history for mer_id: {merchant_id}")

            balance_hist = db.query(db_models.LedgerTransaction).filter(
                db_models.LedgerTransaction.merchant_id == merchant_id
            ).order_by(db_models.LedgerTransaction.created_at.desc()).all()

            if not balance_hist:
                logger.warning(f"No balance history was found for mer_id: {merchant_id}'s account")
                return []

            return balance_hist

        except Exception as e:
            logger.error(f"Exception: {e} while getting a merchant account balance history")
            raise DatabaseError(f"Exception: {e} while getting a merchant account balance history")

    @staticmethod
    def update_limits(db: Session, merchant_id: str, limits_data: mer.TransactionLimits):
        """Update transaction limits for a merchant."""
        limit_query = db.query(db_models.TransactionLimit).filter(
            db_models.TransactionLimit.merchant_id == merchant_id
        )
        db_limit = limit_query.first()
        if not db_limit:
            return None

        update_data = limits_data.model_dump(exclude_unset=True)
        if update_data:
            limit_query.update(update_data, synchronize_session=False)
            db.flush()
            db.refresh(db_limit)
        return db_limit

    @staticmethod
    def get_fee_structure(db: Session, user_id: int) -> db_models.FeeStructure:
        """
        Get fee structure for a merchant account.

        Args:
            db: Database session
            user_id: User ID to get merchant account and fee structure for

        Returns:
            FeeStructure object

        Raises:
            MerchantAccountNotFoundError: If merchant account is not found
            DatabaseError: If any database error occurs
        """
        try:
            logger.info(f"Getting fee structure for user_id: {user_id}")

            merchant = db.query(db_models.MerchantAccount).filter(
                db_models.MerchantAccount.user_id == user_id
            ).first()

            if not merchant:
                logger.warning(f"Merchant account not found for user_id: {user_id}")
                raise MerchantAccountNotFoundError("Merchant account not found. Please create one first.")

            fee_structure = db.query(db_models.FeeStructure).filter(
                db_models.FeeStructure.merchant_id == merchant.merchant_id
            ).first()

            if not fee_structure:
                logger.warning(f"Fee structure not found for merchant_id: {merchant.merchant_id}, creating default")
                fee_structure = db_models.FeeStructure(
                    merchant_id=merchant.merchant_id
                )
                db.add(fee_structure)
                db.flush()
                db.refresh(fee_structure)
                logger.info(f"Created default fee structure for merchant_id: {merchant.merchant_id}")

            logger.info(f"Successfully retrieved fee structure for merchant_id: {merchant.merchant_id}")
            return fee_structure

        except MerchantAccountNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Exception: {e} while getting fee structure for user_id: {user_id}", exc_info=True)
            raise DatabaseError(f"Failed to retrieve fee structure: {str(e)}")

    @staticmethod
    def get_merchant_settings(db: Session, user_id: int) -> db_models.MerchantSettings:
        """
        Get merchant settings for a merchant account.

        Args:
            db: Database session
            user_id: User ID to get merchant account and settings for

        Returns:
            MerchantSettings object

        Raises:
            MerchantAccountNotFoundError: If merchant account is not found
            DatabaseError: If any database error occurs
        """
        try:
            logger.info(f"Getting merchant settings for user_id: {user_id}")

            merchant = db.query(db_models.MerchantAccount).filter(
                db_models.MerchantAccount.user_id == user_id
            ).first()

            if not merchant:
                logger.warning(f"Merchant account not found for user_id: {user_id}")
                raise MerchantAccountNotFoundError("Merchant account not found. Please create one first.")

            settings = db.query(db_models.MerchantSettings).filter(
                db_models.MerchantSettings.merchant_id == merchant.merchant_id
            ).first()


            if not settings:
                logger.warning(f"Merchant settings not found for merchant_id: {merchant.merchant_id}, creating defaults")
                settings = db_models.MerchantSettings(
                    merchant_id=merchant.merchant_id
                )
                db.add(settings)
                db.flush()
                db.refresh(settings)
                logger.info(f"Created default merchant settings for merchant_id: {merchant.merchant_id}")

            logger.info(f"Successfully retrieved merchant settings for merchant_id: {merchant.merchant_id}")
            return settings

        except MerchantAccountNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Exception: {e} while getting merchant settings for user_id: {user_id}", exc_info=True)
            raise DatabaseError(f"Failed to retrieve merchant settings: {str(e)}")

    @staticmethod
    def update_merchant_settings(db: Session, user_id: int, settings_data: mer.MerchantSettings) -> db_models.MerchantSettings:
        """
        Update merchant settings for a merchant account.

        Args:
            db: Database session
            user_id: User ID to get merchant account for
            settings_data: MerchantSettings schema with updated values

        Returns:
            Updated MerchantSettings object

        Raises:
            MerchantAccountNotFoundError: If merchant account is not found
            DatabaseError: If any database error occurs
        """
        try:
            logger.info(f"Updating merchant settings for user_id: {user_id}")

            merchant = db.query(db_models.MerchantAccount).filter(
                db_models.MerchantAccount.user_id == user_id
            ).first()

            if not merchant:
                logger.warning(f"Merchant account not found for user_id: {user_id}")
                raise MerchantAccountNotFoundError("Merchant account not found. Please create one first.")

            settings_query = db.query(db_models.MerchantSettings).filter(
                db_models.MerchantSettings.merchant_id == merchant.merchant_id
            )

            db_settings = settings_query.first()

            if not db_settings:
                logger.warning(f"Merchant settings not found for merchant_id: {merchant.merchant_id}, creating with provided data")
                db_settings = db_models.MerchantSettings(
                    merchant_id=merchant.merchant_id
                )
                db.add(db_settings)
                db.flush()
                logger.info(f"Created merchant settings for merchant_id: {merchant.merchant_id}")

            update_data = settings_data.model_dump(exclude_unset=True)

            if 'ip_whitelist' in update_data:
                logger.warning("ip_whitelist field is not yet implemented in the database schema")
                update_data.pop('ip_whitelist')

            if update_data:
                for key, value in update_data.items():
                    setattr(db_settings, key, value)

                db.flush()
                db.refresh(db_settings)
                logger.info(f"Successfully updated merchant settings for merchant_id: {merchant.merchant_id}")
            else:

                if not db_settings.id:
                    db.flush()
                logger.info(f"No valid fields to update for merchant_id: {merchant.merchant_id}")

            return db_settings

        except MerchantAccountNotFoundError:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Exception: {e} while updating merchant settings for user_id: {user_id}", exc_info=True)
            raise DatabaseError(f"Failed to update merchant settings: {str(e)}")


    @staticmethod
    def create_api_key(db: Session, user_id: int, key_data: api_key_schema.APIKeyCreate) -> tuple[db_models.APIKey, str]:
        """
        Create a new API key for a merchant.

        Args:
            db: Database session
            user_id: User ID to get merchant account for
            key_data: APIKeyCreate schema with key details

        Returns:
            Tuple of (APIKey object, raw_key_string)

        Raises:
            MerchantAccountNotFoundError: If merchant account is not found
            DatabaseError: If any database error occurs
        """
        try:
            logger.info(f"Creating API key for user_id: {user_id}")

            # Get the merchant account
            merchant = db.query(db_models.MerchantAccount).filter(
                db_models.MerchantAccount.user_id == user_id
            ).first()

            if not merchant:
                logger.warning(f"Merchant account not found for user_id: {user_id}")
                raise MerchantAccountNotFoundError("Merchant account not found. Please create one first.")

            prefix = f"{'pk' if key_data.key_type == 'publishable' else 'sk'}_{key_data.environment}_"

            raw_key = prefix + secrets.token_urlsafe(32)

            hashed_key = hash_password(raw_key)

            new_key = db_models.APIKey(
                merchant_id=merchant.merchant_id,
                name=key_data.name,
                api_key=hashed_key,
                key_prefix=prefix,
                key_type=key_data.key_type,
                environment=key_data.environment,
                is_active=True
            )

            db.add(new_key)
            db.flush()
            db.refresh(new_key)

            logger.info(f"Created API key {new_key.id} ({key_data.key_type}/{key_data.environment}) for merchant {merchant.merchant_id}")

            return new_key, raw_key

        except MerchantAccountNotFoundError:
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Exception: {e} while creating API key for user_id: {user_id}", exc_info=True)
            raise DatabaseError(f"Failed to create API key: {str(e)}")

    @staticmethod
    def get_api_keys(db: Session, user_id: int) -> List[db_models.APIKey]:
        """
        Get all API keys for a merchant (excluding revoked keys by default).

        Args:
            db: Database session
            user_id: User ID to get merchant account for

        Returns:
            List of APIKey objects

        Raises:
            MerchantAccountNotFoundError: If merchant account is not found
            DatabaseError: If any database error occurs
        """
        try:
            logger.info(f"Getting API keys for user_id: {user_id}")

            merchant = db.query(db_models.MerchantAccount).filter(
                db_models.MerchantAccount.user_id == user_id
            ).first()

            if not merchant:
                logger.warning(f"Merchant account not found for user_id: {user_id}")
                raise MerchantAccountNotFoundError("Merchant account not found. Please create one first.")

            api_keys = db.query(db_models.APIKey).filter(
                db_models.APIKey.merchant_id == merchant.merchant_id,
                db_models.APIKey.is_active == True
            ).order_by(db_models.APIKey.created_at.desc()).all()

            logger.info(f"Retrieved {len(api_keys)} API keys for merchant {merchant.merchant_id}")
            return api_keys

        except MerchantAccountNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Exception: {e} while getting API keys for user_id: {user_id}", exc_info=True)
            raise DatabaseError(f"Failed to retrieve API keys: {str(e)}")

    @staticmethod
    def get_api_key_by_id(db: Session, user_id: int, key_id: int) -> db_models.APIKey:
        """
        Get a specific API key by ID.

        Args:
            db: Database session
            user_id: User ID to get merchant account for
            key_id: API key ID

        Returns:
            APIKey object

        Raises:
            MerchantAccountNotFoundError: If merchant account is not found
            ResourceNotFoundError: If API key is not found
            DatabaseError: If any database error occurs
        """
        try:
            logger.info(f"Getting API key {key_id} for user_id: {user_id}")

            merchant = db.query(db_models.MerchantAccount).filter(
                db_models.MerchantAccount.user_id == user_id
            ).first()

            if not merchant:
                logger.warning(f"Merchant account not found for user_id: {user_id}")
                raise MerchantAccountNotFoundError("Merchant account not found. Please create one first.")

            api_key = db.query(db_models.APIKey).filter(
                db_models.APIKey.id == key_id,
                db_models.APIKey.merchant_id == merchant.merchant_id
            ).first()

            if not api_key:
                logger.warning(f"API key {key_id} not found for merchant {merchant.merchant_id}")
                raise ResourceNotFoundError("API key not found")

            logger.info(f"Retrieved API key {key_id} for merchant {merchant.merchant_id}")
            return api_key

        except (MerchantAccountNotFoundError, ResourceNotFoundError):
            raise
        except Exception as e:
            logger.error(f"Exception: {e} while getting API key {key_id} for user_id: {user_id}", exc_info=True)
            raise DatabaseError(f"Failed to retrieve API key: {str(e)}")

    @staticmethod
    def update_api_key(db: Session, user_id: int, key_id: int, update_data: api_key_schema.APIKeyUpdate) -> db_models.APIKey:
        """
        Update an API key (name only - keys themselves are immutable).

        Args:
            db: Database session
            user_id: User ID to get merchant account for
            key_id: API key ID
            update_data: APIKeyUpdate schema with new name

        Returns:
            Updated APIKey object

        Raises:
            MerchantAccountNotFoundError: If merchant account is not found
            ResourceNotFoundError: If API key is not found
            DatabaseError: If any database error occurs
        """
        try:
            logger.info(f"Updating API key {key_id} for user_id: {user_id}")

            api_key = MerchantService.get_api_key_by_id(db, user_id, key_id)

            api_key.name = update_data.name

            db.flush()
            db.refresh(api_key)

            logger.info(f"Updated API key {key_id} name to '{update_data.name}'")
            return api_key

        except (MerchantAccountNotFoundError, ResourceNotFoundError):
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Exception: {e} while updating API key {key_id} for user_id: {user_id}", exc_info=True)
            raise DatabaseError(f"Failed to update API key: {str(e)}")

    @staticmethod
    def revoke_api_key(db: Session, user_id: int, key_id: int, reason: str = None) -> db_models.APIKey:
        """
        Revoke an API key (soft delete - marks as inactive).

        Args:
            db: Database session
            user_id: User ID to get merchant account for
            key_id: API key ID
            reason: Optional reason for revocation

        Returns:
            Revoked APIKey object

        Raises:
            MerchantAccountNotFoundError: If merchant account is not found
            ResourceNotFoundError: If API key is not found
            DatabaseError: If any database error occurs
        """
        try:
            logger.info(f"Revoking API key {key_id} for user_id: {user_id}")

            api_key = MerchantService.get_api_key_by_id(db, user_id, key_id)

            if not api_key.is_active:
                logger.warning(f"API key {key_id} is already revoked")
                raise DatabaseError("API key is already revoked")

            api_key.is_active = False
            api_key.revoked_at = datetime.now(timezone.utc)
            api_key.revoke_reason = reason

            db.flush()
            db.refresh(api_key)

            logger.info(f"Revoked API key {key_id} - Reason: {reason or 'Not specified'}")
            return api_key

        except (MerchantAccountNotFoundError, ResourceNotFoundError):
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Exception: {e} while revoking API key {key_id} for user_id: {user_id}", exc_info=True)
            raise DatabaseError(f"Failed to revoke API key: {str(e)}")

    @staticmethod
    def roll_api_key(db: Session, user_id: int, key_id: int) -> tuple[db_models.APIKey, str]:
        """
        Roll/regenerate an API key (creates new key with same settings, revokes old one).

        Args:
            db: Database session
            user_id: User ID to get merchant account for
            key_id: API key ID to roll

        Returns:
            Tuple of (new APIKey object, raw_key_string)

        Raises:
            MerchantAccountNotFoundError: If merchant account is not found
            ResourceNotFoundError: If API key is not found
            DatabaseError: If any database error occurs
        """
        try:
            logger.info(f"Rolling API key {key_id} for user_id: {user_id}")

            old_key = MerchantService.get_api_key_by_id(db, user_id, key_id)

            if not old_key.is_active:
                logger.warning(f"Cannot roll revoked API key {key_id}")
                raise DatabaseError("Cannot roll a revoked API key")
            new_key_data = api_key_schema.APIKeyCreate(
                name=f"{old_key.name} (rolled)",
                key_type=old_key.key_type,
                environment=old_key.environment
            )

            new_key, raw_key = MerchantService.create_api_key(db, user_id, new_key_data)

            old_key.is_active = False
            old_key.revoked_at = datetime.now(timezone.utc)
            old_key.revoke_reason = f"Rolled to new key (ID: {new_key.id})"

            db.flush()

            logger.info(f"Rolled API key {key_id} to new key {new_key.id}")
            return new_key, raw_key

        except (MerchantAccountNotFoundError, ResourceNotFoundError):
            raise
        except Exception as e:
            db.rollback()
            logger.error(f"Exception: {e} while rolling API key {key_id} for user_id: {user_id}", exc_info=True)
            raise DatabaseError(f"Failed to roll API key: {str(e)}")
