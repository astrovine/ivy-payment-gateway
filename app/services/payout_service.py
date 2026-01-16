from typing import List
from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

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
    async def _set_primary_account(db: AsyncSession, merchant_id: str, new_primary_account_id: int):
        logger.info(f"Setting primary account {new_primary_account_id} for merchant {merchant_id}")
        await db.execute(
            update(db_models.PayoutAccount)
            .where(
                db_models.PayoutAccount.merchant_id == merchant_id,
                db_models.PayoutAccount.id != new_primary_account_id
            )
            .values(is_primary=False)
        )

    @staticmethod
    async def _get_merchant_details(db: AsyncSession, user: db_models.User) -> db_models.MerchantAccount:
        from sqlalchemy.orm import selectinload
        result = await db.execute(
            select(db_models.User)
            .options(selectinload(db_models.User.merchant_info), selectinload(db_models.User.verified_info))
            .where(db_models.User.email == user.email)
        )
        user_details = result.scalar_one_or_none()
        if not user_details:
            logger.warning(f"User not found for {user.email}")
            raise ex.PermissionDeniedError

        if not user_details.merchant_info or not user_details.verified_info:
            logger.warning(f"{user.email} doesnt have a merchant account or isn't verified.")
            raise ex.MerchantAccountNotFoundError

        merch_result = await db.execute(select(db_models.MerchantAccount).where(db_models.MerchantAccount.user_id == user_details.id))
        merchant_details = merch_result.scalar_one_or_none()
        if not merchant_details:
            logger.warning(f"No merchant details found for {user.email}, user_id {user_details.id}")
            raise ex.MerchantAccountNotFoundError

        return merchant_details

    @staticmethod
    async def create_payout_account(db: AsyncSession, account: payout.PayoutAccountCreate, user: db_models.User) -> db_models.PayoutAccount:
        user_email = user.email  # Store before any DB operations
        logger.info(f"Creating payout account {user_email}")
        try:
            merchant_details = await PayoutAccountService._get_merchant_details(db, user)

            if not merchant_details.kyc_info or not merchant_details.identity_info or not merchant_details.business_info:
                logger.warning(f"{merchant_details.merchant_id} is not fully verified yet (KYC, Identity, Business), and therefore is not allowed to create an account")
                raise ex.PermissionDeniedError

            accounts_result = await db.execute(select(db_models.PayoutAccount).where(db_models.PayoutAccount.merchant_id == merchant_details.merchant_id))
            payout_account_details = accounts_result.scalars().all()
            existing_account_numbers = [pa.account_number for pa in payout_account_details]

            if account.account_number in existing_account_numbers:
                logger.warning(f'User already has an existing account linked to that account number.')
                raise ex.PermissionDeniedError

            logger.info(f'Creating new payout account for {user_email} (Merchant: {merchant_details.merchant_id})')
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
            await db.commit()
            await db.refresh(new_pay_account)

            if new_pay_account.is_primary:
                await PayoutAccountService._set_primary_account(db, merchant_details.merchant_id, new_pay_account.id)
                await db.commit()
                await db.refresh(new_pay_account)
            elif not payout_account_details:
                logger.info("This is the first account, setting to primary.")
                new_pay_account.is_primary = True
                await db.commit()
                await db.refresh(new_pay_account)

            return new_pay_account
        except Exception as e:
            logger.error(f"Error creating payout account for {user_email}: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def list_payout_accounts(db: AsyncSession, user: db_models.User) -> List[db_models.PayoutAccount]:
        user_email = user.email  # Store before any DB operations
        logger.info(f"Listing payout accounts for {user_email}")
        merchant_details = await PayoutAccountService._get_merchant_details(db, user)

        result = await db.execute(select(db_models.PayoutAccount).where(db_models.PayoutAccount.merchant_id == merchant_details.merchant_id))
        accounts = result.scalars().all()
        logger.info(f"Found {len(accounts)} payout accounts for {user_email}")
        return list(accounts)

    @staticmethod
    async def get_payout_account(db: AsyncSession, user: db_models.User, account_id: int) -> db_models.PayoutAccount:
        user_email = user.email  # Store before any DB operations
        logger.info(f"Getting payout account {account_id} for {user_email}")
        merchant_details = await PayoutAccountService._get_merchant_details(db, user)

        result = await db.execute(select(db_models.PayoutAccount).where(db_models.PayoutAccount.id == account_id))
        db_account = result.scalar_one_or_none()

        if not db_account:
            logger.warning(f"Payout account {account_id} not found.")
            raise ex.ServiceUnavailableError

        if db_account.merchant_id != merchant_details.merchant_id:
            logger.warning(f"User {user_email} does not have permission to access account {account_id}.")
            raise ex.PermissionDeniedError

        return db_account

    @staticmethod
    async def update_payout_account(db: AsyncSession, user: db_models.User, account_id: int, account_update: payout.PayoutAccountUpdate) -> db_models.PayoutAccount:
        user_email = user.email  # Store before any DB operations
        logger.info(f"Updating payout account {account_id} for {user_email}")

        db_account = await PayoutAccountService.get_payout_account(db, user, account_id)

        update_data = account_update.model_dump(exclude_unset=True)
        if not update_data:
            logger.warning(f"No update data provided for account {account_id}.")
            return db_account

        try:
            if 'is_primary' in update_data:
                if update_data['is_primary'] is True:
                    await PayoutAccountService._set_primary_account(db, db_account.merchant_id, db_account.id)
                    db_account.is_primary = True
                elif update_data['is_primary'] is False and db_account.is_primary:
                    raise ex.InvalidRequestError("Cannot unset primary account. Set another account as primary instead.")

            if 'account_holder_name' in update_data:
                db_account.account_holder_name = update_data['account_holder_name']

            db.add(db_account)
            await db.commit()
            await db.refresh(db_account)
            logger.info(f"Successfully updated account {account_id}")
            return db_account
        except Exception as e:
            logger.error(f"Error updating payout account {account_id}: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def delete_payout_account(db: AsyncSession, user: db_models.User, account_id: int) -> db_models.PayoutAccount:
        user_email = user.email  # Store before any DB operations
        logger.info(f"Deleting payout account {account_id} for {user_email}")

        db_account = await PayoutAccountService.get_payout_account(db, user, account_id)

        if db_account.is_primary:
            logger.warning(f"User {user_email} attempting to delete primary account {account_id}.")
            raise ex.PermissionDeniedError("Cannot delete the primary payout account. Please set another account as primary first.")

        try:
            await db.delete(db_account)
            await db.commit()
            logger.info(f"Successfully deleted account {account_id}")
            return db_account
        except Exception as e:
            logger.error(f"Error deleting payout account {account_id}: {e}")
            await db.rollback()
            raise


class PayoutService:
    @staticmethod
    async def create_payout(db: AsyncSession, user_id: int, amount: Decimal, currency: str, account: db_models.PayoutAccount) -> db_models.Payout:
        merchant = await MerchantService.get_merchant_account(db=db, user_id=user_id)
        if currency != merchant.currency:
            logger.warning(f"Payout currency {currency} does not match merchant currency {merchant.currency} for merchant {merchant.merchant_id}")
            raise ex.InvalidRequestError(f"Payout currency must match merchant currency ({merchant.currency})")

        if amount > merchant.available_balance:
            raise InsufficientFundsError()

        new_payout = db_models.Payout(
            merchant_id=merchant.merchant_id,
            payout_account_id=account.id,
            amount=amount,
            currency=currency,
            status=db_models.PayoutStatus.PENDING,
        )
        db.add(new_payout)
        await db.flush()

        available_result = await db.execute(
            select(db_models.Account)
            .where(
                db_models.Account.merchant_id == merchant.merchant_id,
                db_models.Account.account_type == db_models.AccountType.MERCHANT_AVAILABLE,
                db_models.Account.currency == currency
            )
            .with_for_update()
        )
        available_acct = available_result.scalar_one_or_none()

        payable_result = await db.execute(
            select(db_models.Account)
            .where(
                db_models.Account.account_type == db_models.AccountType.PLATFORM_PAYABLE,
                db_models.Account.currency == currency
            )
            .with_for_update()
        )
        payable_acct = payable_result.scalar_one_or_none()

        fee_amount = (amount * FEE_RATE).quantize(Decimal("0.0001"))
        if not available_acct or available_acct.balance < (amount + (fee_amount if fee_amount else Decimal('0'))):
            raise InsufficientFundsError()
        if not payable_acct:
            payable_acct = db_models.Account(account_type=db_models.AccountType.PLATFORM_PAYABLE, currency=currency, balance=0)
            db.add(payable_acct)
            await db.flush()

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

        try:
            db.add(ledger_entry)
            available_acct.balance -= amount
            payable_acct.balance += amount
            merchant.available_balance -= amount

            if fee_amount and fee_amount > 0:
                rev_result = await db.execute(
                    select(db_models.Account)
                    .where(
                        db_models.Account.account_type == db_models.AccountType.PLATFORM_REVENUE,
                        db_models.Account.currency == currency
                    )
                    .with_for_update()
                )
                platform_revenue_acct = rev_result.scalar_one_or_none()
                if not platform_revenue_acct:
                    platform_revenue_acct = db_models.Account(account_type=db_models.AccountType.PLATFORM_REVENUE, currency=currency, balance=0)
                    db.add(platform_revenue_acct)
                    await db.flush()

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
                available_acct.balance -= fee_amount
                platform_revenue_acct.balance += fee_amount
                merchant.available_balance -= fee_amount

            audit = db_models.AuditLog(
                user_id=merchant.user_id,
                merchant_id=merchant.merchant_id,
                action="PAYOUT_CREATED",
                resource_type="PAYOUT",
                resource_id=str(new_payout.id),
                extra_data=str({"amount": str(new_payout.amount), "currency": new_payout.currency})
            )
            db.add(audit)
            await db.flush()

            await db.commit()
            await db.refresh(new_payout)

            process_payout_task.delay(payout_id=new_payout.id)
            return new_payout
        except Exception as e:
            logger.error(f"Error during payout creation transaction: {e}", exc_info=True)
            await db.rollback()
            raise

    @staticmethod
    async def list_payouts(db: AsyncSession, user_id: int):
        merchant = await MerchantService.get_merchant_account(db=db, user_id=user_id)
        result = await db.execute(
            select(db_models.Payout)
            .where(db_models.Payout.merchant_id == merchant.merchant_id)
            .order_by(db_models.Payout.created_at.desc())
        )
        return result.scalars().all()

    @staticmethod
    async def get_payout(db: AsyncSession, user_id: int, payout_id: int) -> db_models.Payout:
        merchant = await MerchantService.get_merchant_account(db=db, user_id=user_id)
        result = await db.execute(select(db_models.Payout).where(db_models.Payout.id == payout_id))
        payout_obj = result.scalar_one_or_none()
        if not payout_obj or payout_obj.merchant_id != merchant.merchant_id:
            raise ex.ResourceNotFoundError("Payout not found")
        return payout_obj

    @staticmethod
    async def cancel_payout(db: AsyncSession, user_id: int, payout_id: int) -> db_models.Payout:
        payout_obj = await PayoutService.get_payout(db=db, user_id=user_id, payout_id=payout_id)
        current_status = getattr(payout_obj, 'status', None)
        if current_status != db_models.PayoutStatus.PENDING and current_status != db_models.PayoutStatus.PENDING.name and current_status != db_models.PayoutStatus.PENDING.value:
            raise ex.InvalidRequestError("Only pending payouts can be cancelled")

        ledger_result = await db.execute(select(db_models.LedgerTransaction).where(db_models.LedgerTransaction.payout_id == payout_obj.id))
        existing_ledgers = ledger_result.scalars().all()

        try:
            if existing_ledgers:
                for l in existing_ledgers:
                    rev = db_models.LedgerTransaction(
                        payout_id=payout_obj.id,
                        merchant_id=payout_obj.merchant_id,
                        transaction_type=db_models.TransactionType.FEE,
                        amount=-l.amount,
                        currency=l.currency,
                        debit_account_id=l.credit_account_id,
                        credit_account_id=l.debit_account_id,
                        description=f"Reversal for cancelled payout {payout_obj.id}"
                    )
                    db.add(rev)

                    da_result = await db.execute(select(db_models.Account).where(db_models.Account.id == l.debit_account_id))
                    da = da_result.scalar_one_or_none()
                    ca_result = await db.execute(select(db_models.Account).where(db_models.Account.id == l.credit_account_id))
                    ca = ca_result.scalar_one_or_none()
                    if da and ca:
                        da.balance += l.amount
                        ca.balance -= l.amount

            payout_obj.status = db_models.PayoutStatus.FAILED
            payout_obj.failure_reason = "cancelled_by_user"
            db.add(payout_obj)

            audit = db_models.AuditLog(
                user_id=payout_obj.merchant.user_id if payout_obj.merchant else None,
                merchant_id=payout_obj.merchant_id,
                action="PAYOUT_CANCELLED",
                resource_type="PAYOUT",
                resource_id=str(payout_obj.id),
                extra_data=str({"reason": payout_obj.failure_reason})
            )
            db.add(audit)

            await db.commit()
            await db.refresh(payout_obj)
            return payout_obj
        except Exception as e:
            await db.rollback()
            logger.error(f"Error cancelling payout {payout_id}: {e}", exc_info=True)
            raise

    @staticmethod
    async def _aggregate_settlement_for_payout(db: AsyncSession, payout_obj: db_models.Payout):
        result = await db.execute(select(db_models.LedgerTransaction).where(db_models.LedgerTransaction.payout_id == payout_obj.id))
        ledger_rows = result.scalars().all()

        total_transactions = len(ledger_rows)
        total_amount = Decimal('0')
        total_fees = Decimal('0')
        total_refunds = Decimal('0')
        total_chargebacks = Decimal('0')
        for lr in ledger_rows:
            ttype = lr.transaction_type
            if ttype == db_models.TransactionType.PAYOUT or (hasattr(ttype, 'name') and ttype.name == 'PAYOUT'):
                total_amount += lr.amount
            elif ttype == db_models.TransactionType.FEE or (hasattr(ttype, 'name') and ttype.name == 'FEE'):
                total_fees += lr.amount
            elif ttype == db_models.TransactionType.REFUND or (hasattr(ttype, 'name') and ttype.name == 'REFUND'):
                total_refunds += lr.amount
            elif ttype == db_models.TransactionType.CHARGE or (hasattr(ttype, 'name') and ttype.name == 'CHARGE'):
                total_amount += lr.amount

        net_settlement = total_amount - total_fees - total_refunds - total_chargebacks
        return {
            "merchant_id": payout_obj.merchant_id,
            "settlement_period_start": payout_obj.created_at,
            "settlement_period_end": payout_obj.processed_at or payout_obj.created_at,
            "total_transactions": total_transactions,
            "total_amount": total_amount,
            "total_fees": total_fees,
            "total_refunds": total_refunds,
            "total_chargebacks": total_chargebacks,
            "net_settlement": net_settlement,
            "currency": payout_obj.currency,
            "status": payout_obj.status.value if hasattr(payout_obj.status, 'value') else str(payout_obj.status),
            "payout_id": payout_obj.id,
            "id": payout_obj.id,
            "created_at": payout_obj.created_at,
            "completed_at": payout_obj.processed_at,
        }

    @staticmethod
    async def list_settlement_reports(db: AsyncSession, user_id: int):
        merchant = await MerchantService.get_merchant_account(db=db, user_id=user_id)
        result = await db.execute(
            select(db_models.Payout)
            .where(db_models.Payout.merchant_id == merchant.merchant_id)
            .order_by(db_models.Payout.created_at.desc())
        )
        payouts = result.scalars().all()
        reports = []
        for p in payouts:
            report = await PayoutService._aggregate_settlement_for_payout(db, p)
            reports.append(report)
        return reports

    @staticmethod
    async def get_settlement_report(db: AsyncSession, user_id: int, payout_id: int):
        merchant = await MerchantService.get_merchant_account(db=db, user_id=user_id)
        result = await db.execute(select(db_models.Payout).where(db_models.Payout.id == payout_id))
        payout_obj = result.scalar_one_or_none()
        if not payout_obj or payout_obj.merchant_id != merchant.merchant_id:
            raise ex.ResourceNotFoundError("Settlement report not found")
        return await PayoutService._aggregate_settlement_for_payout(db, payout_obj)

    @staticmethod
    async def get_settlement_schedule(db: AsyncSession, user_id: int):
        merchant = await MerchantService.get_merchant_account(db=db, user_id=user_id)
        return {
            "merchant_id": merchant.merchant_id,
            "schedule": merchant.settlement_schedule,
            "delay_days": merchant.settlement_delay_days,
            "minimum_payout_amount": merchant.minimum_payout_amount,
            "next_settlement_date": merchant.next_settlement_date,
            "updated_at": merchant.updated_at,
        }

    @staticmethod
    async def update_settlement_schedule(db: AsyncSession, user_id: int, schedule: dict):
        merchant = await MerchantService.get_merchant_account(db=db, user_id=user_id)
        if 'schedule' in schedule:
            merchant.settlement_schedule = schedule['schedule']
        if 'delay_days' in schedule:
            merchant.settlement_delay_days = schedule['delay_days']
        if 'minimum_payout_amount' in schedule:
            merchant.minimum_payout_amount = schedule['minimum_payout_amount']
        db.add(merchant)
        await db.commit()
        await db.refresh(merchant)
        return await PayoutService.get_settlement_schedule(db=db, user_id=user_id)

    @staticmethod
    async def process_payout_now(db: AsyncSession, payout_id: int, triggered_by_user_id: int = None):
        result = await db.execute(select(db_models.Payout).where(db_models.Payout.id == payout_id).with_for_update())
        payout_obj = result.scalar_one_or_none()
        if not payout_obj:
            raise ex.ResourceNotFoundError("Payout not found")

        current_status = getattr(payout_obj, 'status', None)
        pending_match = current_status == db_models.PayoutStatus.PENDING or current_status == getattr(db_models.PayoutStatus.PENDING, 'name', None) or current_status == getattr(db_models.PayoutStatus.PENDING, 'value', None)
        if not pending_match:
            raise ex.InvalidRequestError("Payout is not pending")

        ledger_result = await db.execute(select(db_models.LedgerTransaction).where(db_models.LedgerTransaction.payout_id == payout_obj.id))
        existing_ledgers = ledger_result.scalars().all()

        try:
            if existing_ledgers:
                payout_obj.status = db_models.PayoutStatus.SUCCEEDED
                payout_obj.processed_at = func.now()
                db.add(payout_obj)
                audit = db_models.AuditLog(
                    user_id=triggered_by_user_id,
                    merchant_id=payout_obj.merchant_id,
                    action="PAYOUT_PROCESSED",
                    resource_type="PAYOUT",
                    resource_id=str(payout_obj.id),
                    extra_data=str({"amount": str(payout_obj.amount), "currency": payout_obj.currency, "note": "finalized reservation"})
                )
                db.add(audit)
                await db.commit()
                return payout_obj

            avail_result = await db.execute(
                select(db_models.Account)
                .where(
                    db_models.Account.merchant_id == payout_obj.merchant_id,
                    db_models.Account.account_type == db_models.AccountType.MERCHANT_AVAILABLE,
                    db_models.Account.currency == payout_obj.currency
                )
                .with_for_update()
            )
            available_acct = avail_result.scalar_one_or_none()

            pay_result = await db.execute(
                select(db_models.Account)
                .where(
                    db_models.Account.account_type == db_models.AccountType.PLATFORM_PAYABLE,
                    db_models.Account.currency == payout_obj.currency
                )
                .with_for_update()
            )
            payable_acct = pay_result.scalar_one_or_none()

            if not available_acct or not payable_acct:
                payout_obj.status = db_models.PayoutStatus.FAILED
                payout_obj.failure_reason = "Internal platform accounting error."
                db.add(payout_obj)
                await db.commit()
                raise ex.ServiceUnavailableError("Missing ledger accounts for payout currency")

            fee_amount = (payout_obj.amount * FEE_RATE).quantize(Decimal("0.0001"))
            if available_acct.balance < (payout_obj.amount + (fee_amount if fee_amount else Decimal('0'))):
                payout_obj.status = db_models.PayoutStatus.FAILED
                payout_obj.failure_reason = "Insufficient funds at time of processing."
                db.add(payout_obj)
                await db.commit()
                raise ex.InsufficientFundsError()

            rev_result = await db.execute(
                select(db_models.Account)
                .where(
                    db_models.Account.account_type == db_models.AccountType.PLATFORM_REVENUE,
                    db_models.Account.currency == payout_obj.currency
                )
                .with_for_update()
            )
            platform_revenue_acct = rev_result.scalar_one_or_none()
            if not platform_revenue_acct:
                platform_revenue_acct = db_models.Account(account_type=db_models.AccountType.PLATFORM_REVENUE, currency=payout_obj.currency, balance=0)
                db.add(platform_revenue_acct)
                await db.flush()

            payout_ledger = db_models.LedgerTransaction(
                payout_id=payout_obj.id,
                transaction_type=db_models.TransactionType.PAYOUT,
                description=f"Payout {payout_obj.id} to {payout_obj.payout_account_id}",
                amount=payout_obj.amount,
                currency=payout_obj.currency,
                debit_account_id=available_acct.id,
                credit_account_id=payable_acct.id
            )
            db.add(payout_ledger)

            if fee_amount and fee_amount > 0:
                fee_ledger = db_models.LedgerTransaction(
                    payout_id=payout_obj.id,
                    transaction_type=db_models.TransactionType.FEE,
                    description=f"Payout fee for {payout_obj.id}",
                    amount=fee_amount,
                    currency=payout_obj.currency,
                    debit_account_id=available_acct.id,
                    credit_account_id=platform_revenue_acct.id
                )
                db.add(fee_ledger)

            available_acct.balance -= (payout_obj.amount + (fee_amount if fee_amount else Decimal('0')))
            payable_acct.balance += payout_obj.amount
            platform_revenue_acct.balance += (fee_amount if fee_amount else Decimal('0'))
            if payout_obj.merchant:
                payout_obj.merchant.available_balance -= (payout_obj.amount + (fee_amount if fee_amount else Decimal('0')))

            payout_obj.status = db_models.PayoutStatus.SUCCEEDED
            payout_obj.processed_at = func.now()
            db.add(payout_obj)

            audit = db_models.AuditLog(
                user_id=triggered_by_user_id,
                merchant_id=payout_obj.merchant_id,
                action="PAYOUT_PROCESSED",
                resource_type="PAYOUT",
                resource_id=str(payout_obj.id),
                extra_data=str({"amount": str(payout_obj.amount), "fee": str(fee_amount), "currency": payout_obj.currency})
            )
            db.add(audit)
            await db.commit()
            await db.refresh(payout_obj)
            return payout_obj
        except Exception:
            await db.rollback()
            raise
