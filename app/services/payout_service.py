from typing import List

from sqlalchemy import func
from sqlalchemy.orm import Session
from decimal import Decimal
from app.models import db_models
from app.schemas import payout
from app.services.merchant_service import MerchantService
from app.utilities import exceptions as ex
from app.utilities.exceptions import InsufficientFundsError
from app.utilities.logger import setup_logger
from app.tasks import process_payout_task

logger = setup_logger(__name__)

FEE_RATE = Decimal("0.005")


class PayoutAccountService:

    @staticmethod
    def _set_primary_account(db: Session, merchant_id: str, new_primary_account_id: int):
        logger.info(f"Setting primary account {new_primary_account_id} for merchant {merchant_id}")
        db.query(db_models.PayoutAccount).filter(
            db_models.PayoutAccount.merchant_id == merchant_id,
            db_models.PayoutAccount.id != new_primary_account_id
        ).update({"is_primary": False})

    @staticmethod
    def _get_merchant_details(db: Session, user: db_models.User) -> db_models.MerchantAccount:
        user_details = db.query(db_models.User).filter(db_models.User.email == user.email).first()
        if not user_details:
            logger.warning(f"User not found for {user.email}")
            raise ex.PermissionDeniedError

        if not user_details.merchant_info or not user_details.verified_info:
            logger.warning(f"{user.email} doesnt have a merchant account or isn't verified.")
            raise ex.MerchantAccountNotFoundError

        merchant_details = db.query(db_models.MerchantAccount).filter(
            db_models.MerchantAccount.user_id == user_details.id).first()
        if not merchant_details:
            logger.warning(f"No merchant details found for {user.email}, user_id {user_details.id}")
            raise ex.MerchantAccountNotFoundError

        return merchant_details

    @staticmethod
    def create_payout_account(db: Session, account: payout.PayoutAccountCreate,
                              user: db_models.User) -> db_models.PayoutAccount:
        logger.info(f"Creating payout account {user.email}")
        try:
            merchant_details = PayoutAccountService._get_merchant_details(db, user)

            if not merchant_details.kyc_info or not merchant_details.identity_info or not merchant_details.business_info:
                logger.warning(
                    f"{merchant_details.merchant_id} is not fully verified yet (KYC, Identity, Business), and therefore is not allowed to create an account")
                raise ex.PermissionDeniedError

            payout_account_details = db.query(db_models.PayoutAccount).filter(
                db_models.PayoutAccount.merchant_id == merchant_details.merchant_id).all()
            existing_account_numbers = [pa.account_number for pa in payout_account_details]

            if account.account_number in existing_account_numbers:
                logger.warning(f'User already has an existing account linked to that account number.')
                raise ex.PermissionDeniedError

            logger.info(f'Creating new payout account for {user.email} (Merchant: {merchant_details.merchant_id})')
            new_pay_account = db_models.PayoutAccount(
                merchant_id=merchant_details.merchant_id,
                account_holder_name=account.account_holder_name,
                account_number=account.account_number,
                account_number_last4=account.account_number[-4:],
                routing_number=account.routing_number,
                bank_name=account.bank_name,
                bank_country=account.bank_country,
                currency=account.currency,
                account_type=account.account_type,
                is_primary=account.is_primary,
                is_verified=False,
                verification_status="pending"
            )

            db.add(new_pay_account)
            db.commit()
            db.refresh(new_pay_account)

            if new_pay_account.is_primary:
                PayoutAccountService._set_primary_account(db, merchant_details.merchant_id, new_pay_account.id)
                db.commit()
                db.refresh(new_pay_account)
            elif not payout_account_details:
                logger.info("This is the first account, setting to primary.")
                new_pay_account.is_primary = True
                db.commit()
                db.refresh(new_pay_account)

            return new_pay_account
        except Exception as e:
            logger.error(f"Error creating payout account for {user.email}: {e}")
            db.rollback()
            raise

    @staticmethod
    def list_payout_accounts(db: Session, user: db_models.User) -> List[db_models.PayoutAccount]:
        logger.info(f"Listing payout accounts for {user.email}")
        merchant_details = PayoutAccountService._get_merchant_details(db, user)

        accounts = db.query(db_models.PayoutAccount).filter(
            db_models.PayoutAccount.merchant_id == merchant_details.merchant_id).all()
        logger.info(f"Found {len(accounts)} payout accounts for {user.email}")
        return accounts

    @staticmethod
    def get_payout_account(db: Session, user: db_models.User, account_id: int) -> db_models.PayoutAccount:
        logger.info(f"Getting payout account {account_id} for {user.email}")
        merchant_details = PayoutAccountService._get_merchant_details(db, user)

        db_account = db.query(db_models.PayoutAccount).filter(db_models.PayoutAccount.id == account_id).first()

        if not db_account:
            logger.warning(f"Payout account {account_id} not found.")
            raise ex.ServiceUnavailableError

        if db_account.merchant_id != merchant_details.merchant_id:
            logger.warning(f"User {user.email} does not have permission to access account {account_id}.")
            raise ex.PermissionDeniedError

        return db_account

    @staticmethod
    def update_payout_account(db: Session, user: db_models.User, account_id: int,
                              account_update: payout.PayoutAccountUpdate) -> db_models.PayoutAccount:
        logger.info(f"Updating payout account {account_id} for {user.email}")

        db_account = PayoutAccountService.get_payout_account(db, user, account_id)

        update_data = account_update.model_dump(exclude_unset=True)
        if not update_data:
            logger.warning(f"No update data provided for account {account_id}.")
            return db_account

        try:
            if 'is_primary' in update_data:
                if update_data['is_primary'] is True:
                    PayoutAccountService._set_primary_account(db, db_account.merchant_id, db_account.id)
                    db_account.is_primary = True
                elif update_data['is_primary'] is False and db_account.is_primary:
                    raise ex.InvalidRequestError(
                        "Cannot unset primary account. Set another account as primary instead.")

            if 'account_holder_name' in update_data:
                db_account.account_holder_name = update_data['account_holder_name']

            db.add(db_account)
            db.commit()
            db.refresh(db_account)
            logger.info(f"Successfully updated account {account_id}")
            return db_account
        except Exception as e:
            logger.error(f"Error updating payout account {account_id}: {e}")
            db.rollback()
            raise

    @staticmethod
    def delete_payout_account(db: Session, user: db_models.User, account_id: int) -> db_models.PayoutAccount:
        logger.info(f"Deleting payout account {account_id} for {user.email}")

        db_account = PayoutAccountService.get_payout_account(db, user, account_id)

        if db_account.is_primary:
            logger.warning(f"User {user.email} attempting to delete primary account {account_id}.")
            raise ex.PermissionDeniedError(
                "Cannot delete the primary payout account. Please set another account as primary first.")

        try:
            db.delete(db_account)
            db.commit()
            logger.info(f"Successfully deleted account {account_id}")
            return db_account
        except Exception as e:
            logger.error(f"Error deleting payout account {account_id}: {e}")
            db.rollback()
            raise


class PayoutService:
    @staticmethod
    def create_payout(db: Session, user_id: int, amount: Decimal, currency: str, account: db_models.PayoutAccount) -> db_models.Payout:
        merchant = MerchantService.get_merchant_account(db=db, user_id=user_id)
        # Enforce that payouts use the merchant's configured currency
        if currency != merchant.currency:
            logger.warning(f"Payout currency {currency} does not match merchant currency {merchant.currency} for merchant {merchant.merchant_id}")
            raise ex.InvalidRequestError(f"Payout currency must match merchant currency ({merchant.currency})")

        if amount > merchant.available_balance:
            raise InsufficientFundsError()
        # create payout row and reserve funds immediately by creating a ledger entry
        new_payout = db_models.Payout(
            merchant_id=merchant.merchant_id,
            payout_account_id=account.id,
            amount=amount,
            currency=currency,
            status=db_models.PayoutStatus.PENDING,
        )
        db.add(new_payout)
        db.flush()  # populate new_payout.id

        # find accounts and ensure balances
        available_acct = db.query(db_models.Account).filter(
            db_models.Account.merchant_id == merchant.merchant_id,
            db_models.Account.account_type == db_models.AccountType.MERCHANT_AVAILABLE,
            db_models.Account.currency == currency
        ).with_for_update().first()
        payable_acct = db.query(db_models.Account).filter(
            db_models.Account.account_type == db_models.AccountType.PLATFORM_PAYABLE,
            db_models.Account.currency == currency
        ).with_for_update().first()

        # compute fee before final balance checks
        fee_amount = (amount * FEE_RATE).quantize(Decimal("0.0001"))
        if not available_acct or available_acct.balance < (amount + (fee_amount if fee_amount else Decimal('0'))):
            raise InsufficientFundsError()
        if not payable_acct:
            # create platform payable if missing
            payable_acct = db_models.Account(account_type=db_models.AccountType.PLATFORM_PAYABLE, currency=currency, balance=0)
            db.add(payable_acct)
            db.flush()

        # create ledger entry to record reservation
        ledger_entry = db_models.LedgerTransaction(
            payout_id=new_payout.id,
            merchant_id=merchant.merchant_id,
            transaction_type=db_models.TransactionType.PAYOUT,
            amount=amount,
            currency=currency,
            debit_account_id=available_acct.id,
            credit_account_id=payable_acct.id,
            description=f"Payout reservation {new_payout.id}"
        )

        # Add reservation ledger and apply balances in this transaction
        try:
            db.add(ledger_entry)
            # apply reservation balances: move payout amount from merchant available -> platform payable
            available_acct.balance -= amount
            payable_acct.balance += amount
            merchant.available_balance -= amount

            # create fee ledger (small platform fee) and move fee to PLATFORM_REVENUE
            if fee_amount and fee_amount > 0:
                platform_revenue_acct = db.query(db_models.Account).filter(
                    db_models.Account.account_type == db_models.AccountType.PLATFORM_REVENUE,
                    db_models.Account.currency == currency
                ).with_for_update().first()
                if not platform_revenue_acct:
                    platform_revenue_acct = db_models.Account(account_type=db_models.AccountType.PLATFORM_REVENUE, currency=currency, balance=0)
                    db.add(platform_revenue_acct)
                    db.flush()

                fee_ledger = db_models.LedgerTransaction(
                    payout_id=new_payout.id,
                    merchant_id=merchant.merchant_id,
                    transaction_type=db_models.TransactionType.FEE,
                    amount=fee_amount,
                    currency=currency,
                    debit_account_id=available_acct.id,
                    credit_account_id=platform_revenue_acct.id,
                    description=f"Payout fee {new_payout.id}"
                )
                db.add(fee_ledger)

                # apply fee balances
                available_acct.balance -= fee_amount
                platform_revenue_acct.balance += fee_amount
                merchant.available_balance -= fee_amount

            # create audit log within the same transaction so commit is atomic
            audit = db_models.AuditLog(
                user_id=merchant.user_id,
                merchant_id=merchant.merchant_id,
                action="PAYOUT_CREATED",
                resource_type="PAYOUT",
                resource_id=str(new_payout.id),
                extra_data=str({"amount": str(new_payout.amount), "currency": new_payout.currency})
            )
            db.add(audit)

            # flush to persist ledger entries' IDs before commit for debugging
            db.flush()
            # log ledger ids (if any)
            try:
                # ledger_entry and fee_ledger may now have ids
                logger.info(f"Created payout reservation ledger id: {getattr(ledger_entry, 'id', None)}, fee_ledger id: {getattr(locals().get('fee_ledger', None), 'id', None)} for payout {new_payout.id}")
            except Exception:
                logger.debug("Could not log ledger ids after flush")

            # final commit for payout + ledger + audit
            db.commit()
            db.refresh(new_payout)

            # enqueue background processing (external transfer, webhooks)
            process_payout_task.delay(payout_id=new_payout.id)

            return new_payout
        except Exception as e:
            logger.error(f"Error during payout creation transaction: {e}", exc_info=True)
            db.rollback()
            raise

    @staticmethod
    def list_payouts(db: Session, user_id: int):
        merchant = MerchantService.get_merchant_account(db=db, user_id=user_id)
        payouts = db.query(db_models.Payout).filter(db_models.Payout.merchant_id == merchant.merchant_id).order_by(db_models.Payout.created_at.desc()).all()
        return payouts

    @staticmethod
    def get_payout(db: Session, user_id: int, payout_id: int) -> db_models.Payout:
        merchant = MerchantService.get_merchant_account(db=db, user_id=user_id)
        payout = db.query(db_models.Payout).filter(db_models.Payout.id == payout_id).first()
        if not payout or payout.merchant_id != merchant.merchant_id:
            raise ex.ResourceNotFoundError("Payout not found")
        return payout

    @staticmethod
    def cancel_payout(db: Session, user_id: int, payout_id: int) -> db_models.Payout:
        payout = PayoutService.get_payout(db=db, user_id=user_id, payout_id=payout_id)
        # Only allow cancelling pending payouts
        # Compare against either enum member or its name/value
        current_status = getattr(payout, 'status', None)
        if current_status != db_models.PayoutStatus.PENDING and current_status != db_models.PayoutStatus.PENDING.name and current_status != db_models.PayoutStatus.PENDING.value:
            raise ex.InvalidRequestError("Only pending payouts can be cancelled")

        # If there are ledger reservations, reverse them to restore balances
        existing_ledgers = db.query(db_models.LedgerTransaction).filter(db_models.LedgerTransaction.payout_id == payout.id).all()
        try:
            if existing_ledgers:
                for l in existing_ledgers:
                    # create reversal ledger
                    rev = db_models.LedgerTransaction(
                        payout_id=payout.id,
                        merchant_id=payout.merchant_id,
                        transaction_type=db_models.TransactionType.FEE,
                        amount=-l.amount,
                        currency=l.currency,
                        debit_account_id=l.credit_account_id,
                        credit_account_id=l.debit_account_id,
                        description=f"Reversal for cancelled payout {payout.id}"
                    )
                    db.add(rev)
                    # adjust balances back
                    da = db.query(db_models.Account).get(l.debit_account_id)
                    ca = db.query(db_models.Account).get(l.credit_account_id)
                    if da and ca:
                        da.balance += l.amount
                        ca.balance -= l.amount

            payout.status = db_models.PayoutStatus.FAILED
            payout.failure_reason = "cancelled_by_user"
            db.add(payout)

            # audit
            audit = db_models.AuditLog(
                user_id=payout.merchant.user_id if payout.merchant else None,
                merchant_id=payout.merchant_id,
                action="PAYOUT_CANCELLED",
                resource_type="PAYOUT",
                resource_id=str(payout.id),
                extra_data=str({"reason": payout.failure_reason})
            )
            db.add(audit)

            db.commit()
            db.refresh(payout)
            return payout
        except Exception as e:
            db.rollback()
            logger.error(f"Error cancelling payout {payout_id}: {e}", exc_info=True)
            raise

    @staticmethod
    def _aggregate_settlement_for_payout(db: Session, payout: db_models.Payout):
        # Aggregate ledger transactions tied to this payout
        ledger_rows = db.query(db_models.LedgerTransaction).filter(db_models.LedgerTransaction.payout_id == payout.id).all()
        total_transactions = len(ledger_rows)
        total_amount = Decimal('0')
        total_fees = Decimal('0')
        total_refunds = Decimal('0')
        total_chargebacks = Decimal('0')
        for lr in ledger_rows:
            ttype = lr.transaction_type
            # transaction_type may be an Enum member
            if ttype == db_models.TransactionType.PAYOUT or (hasattr(ttype, 'name') and ttype.name == 'PAYOUT'):
                total_amount += lr.amount
            elif ttype == db_models.TransactionType.FEE or (hasattr(ttype, 'name') and ttype.name == 'FEE'):
                total_fees += lr.amount
            elif ttype == db_models.TransactionType.REFUND or (hasattr(ttype, 'name') and ttype.name == 'REFUND'):
                total_refunds += lr.amount
            elif ttype == db_models.TransactionType.CHARGE or (hasattr(ttype, 'name') and ttype.name == 'CHARGE'):
                # charges are part of settlement flows; include in net if needed
                total_amount += lr.amount

        net_settlement = total_amount - total_fees - total_refunds - total_chargebacks
        return {
            "merchant_id": payout.merchant_id,
            "settlement_period_start": payout.created_at,
            "settlement_period_end": payout.processed_at or payout.created_at,
            "total_transactions": total_transactions,
            "total_amount": total_amount,
            "total_fees": total_fees,
            "total_refunds": total_refunds,
            "total_chargebacks": total_chargebacks,
            "net_settlement": net_settlement,
            "currency": payout.currency,
            "status": payout.status.value if hasattr(payout.status, 'value') else str(payout.status),
            "payout_id": payout.id,
            "id": payout.id,
            "created_at": payout.created_at,
            "completed_at": payout.processed_at,
        }

    @staticmethod
    def list_settlement_reports(db: Session, user_id: int):
        merchant = MerchantService.get_merchant_account(db=db, user_id=user_id)
        payouts = db.query(db_models.Payout).filter(db_models.Payout.merchant_id == merchant.merchant_id).order_by(db_models.Payout.created_at.desc()).all()
        reports = [PayoutService._aggregate_settlement_for_payout(db, p) for p in payouts]
        return reports

    @staticmethod
    def get_settlement_report(db: Session, user_id: int, payout_id: int):
        merchant = MerchantService.get_merchant_account(db=db, user_id=user_id)
        payout = db.query(db_models.Payout).filter(db_models.Payout.id == payout_id).first()
        if not payout or payout.merchant_id != merchant.merchant_id:
            raise ex.ResourceNotFoundError("Settlement report not found")
        return PayoutService._aggregate_settlement_for_payout(db, payout)

    @staticmethod
    def get_settlement_schedule(db: Session, user_id: int):
        merchant = MerchantService.get_merchant_account(db=db, user_id=user_id)
        return {
            "merchant_id": merchant.merchant_id,
            "schedule": merchant.settlement_schedule,
            "delay_days": merchant.settlement_delay_days,
            "minimum_payout_amount": merchant.minimum_payout_amount,
            "next_settlement_date": merchant.next_settlement_date,
            "updated_at": merchant.updated_at,
        }

    @staticmethod
    def update_settlement_schedule(db: Session, user_id: int, schedule: dict):
        merchant = MerchantService.get_merchant_account(db=db, user_id=user_id)
        if 'schedule' in schedule:
            merchant.settlement_schedule = schedule['schedule']
        if 'delay_days' in schedule:
            merchant.settlement_delay_days = schedule['delay_days']
        if 'minimum_payout_amount' in schedule:
            merchant.minimum_payout_amount = schedule['minimum_payout_amount']
        db.add(merchant)
        db.commit()
        db.refresh(merchant)
        return PayoutService.get_settlement_schedule(db=db, user_id=user_id)

    @staticmethod
    def process_payout_now(db: Session, payout_id: int, triggered_by_user_id: int = None):
        """
        Synchronously process a payout (used for admin/manual reconciliation).
        This performs the same actions as `process_payout_task` fallback: finalize reservation if exists, otherwise create ledger rows and apply balances.
        """
        payout = db.query(db_models.Payout).filter(db_models.Payout.id == payout_id).with_for_update().first()
        if not payout:
            raise ex.ResourceNotFoundError("Payout not found")

        # normalize check for pending
        current_status = getattr(payout, 'status', None)
        pending_match = current_status == db_models.PayoutStatus.PENDING or current_status == getattr(db_models.PayoutStatus.PENDING, 'name', None) or current_status == getattr(db_models.PayoutStatus.PENDING, 'value', None)
        if not pending_match:
            raise ex.InvalidRequestError("Payout is not pending")

        existing_ledgers = db.query(db_models.LedgerTransaction).filter(db_models.LedgerTransaction.payout_id == payout.id).all()
        try:
            if existing_ledgers:
                payout.status = db_models.PayoutStatus.SUCCEEDED
                payout.processed_at = func.now()
                db.add(payout)
                audit = db_models.AuditLog(
                    user_id=triggered_by_user_id,
                    merchant_id=payout.merchant_id,
                    action="PAYOUT_PROCESSED",
                    resource_type="PAYOUT",
                    resource_id=str(payout.id),
                    extra_data=str({"amount": str(payout.amount), "currency": payout.currency, "note": "finalized reservation"})
                )
                db.add(audit)
                db.commit()
                return payout

            # fallback: perform ledger move now
            available_acct = db.query(db_models.Account).filter(
                db_models.Account.merchant_id == payout.merchant_id,
                db_models.Account.account_type == db_models.AccountType.MERCHANT_AVAILABLE,
                db_models.Account.currency == payout.currency
            ).with_for_update().first()
            payable_acct = db.query(db_models.Account).filter(
                db_models.Account.account_type == db_models.AccountType.PLATFORM_PAYABLE,
                db_models.Account.currency == payout.currency
            ).with_for_update().first()
            if not available_acct or not payable_acct:
                payout.status = db_models.PayoutStatus.FAILED
                payout.failure_reason = "Internal platform accounting error."
                db.add(payout)
                db.commit()
                raise ex.ServiceUnavailableError("Missing ledger accounts for payout currency")

            # compute fee
            fee_amount = (payout.amount * FEE_RATE).quantize(Decimal("0.0001"))
            if available_acct.balance < (payout.amount + (fee_amount if fee_amount else Decimal('0'))):
                payout.status = db_models.PayoutStatus.FAILED
                payout.failure_reason = "Insufficient funds at time of processing."
                db.add(payout)
                db.commit()
                raise ex.InsufficientFundsError()

            # ensure platform revenue
            platform_revenue_acct = db.query(db_models.Account).filter(
                db_models.Account.account_type == db_models.AccountType.PLATFORM_REVENUE,
                db_models.Account.currency == payout.currency
            ).with_for_update().first()
            if not platform_revenue_acct:
                platform_revenue_acct = db_models.Account(account_type=db_models.AccountType.PLATFORM_REVENUE, currency=payout.currency, balance=0)
                db.add(platform_revenue_acct)
                db.flush()

            payout_ledger = db_models.LedgerTransaction(
                payout_id=payout.id,
                transaction_type=db_models.TransactionType.PAYOUT,
                description=f"Payout {payout.id} to {payout.payout_account_id}",
                amount=payout.amount,
                currency=payout.currency,
                debit_account_id=available_acct.id,
                credit_account_id=payable_acct.id
            )
            db.add(payout_ledger)

            if fee_amount and fee_amount > 0:
                fee_ledger = db_models.LedgerTransaction(
                    payout_id=payout.id,
                    transaction_type=db_models.TransactionType.FEE,
                    description=f"Payout fee for {payout.id}",
                    amount=fee_amount,
                    currency=payout.currency,
                    debit_account_id=available_acct.id,
                    credit_account_id=platform_revenue_acct.id
                )
                db.add(fee_ledger)

            # apply balances
            available_acct.balance -= (payout.amount + (fee_amount if fee_amount else Decimal('0')))
            payable_acct.balance += payout.amount
            platform_revenue_acct.balance += (fee_amount if fee_amount else Decimal('0'))
            if payout.merchant:
                payout.merchant.available_balance -= (payout.amount + (fee_amount if fee_amount else Decimal('0')))

            payout.status = db_models.PayoutStatus.SUCCEEDED
            payout.processed_at = func.now()
            db.add(payout)

            audit = db_models.AuditLog(
                user_id=triggered_by_user_id,
                merchant_id=payout.merchant_id,
                action="PAYOUT_PROCESSED",
                resource_type="PAYOUT",
                resource_id=str(payout.id),
                extra_data=str({"amount": str(payout.amount), "fee": str(fee_amount), "currency": payout.currency})
            )
            db.add(audit)
            db.commit()
            db.refresh(payout)
            return payout
        except Exception:
            db.rollback()
            raise
