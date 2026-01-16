from decimal import Decimal
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import db_models
from ..models.enums import AccountType
from ..utilities.logger import setup_logger

logger = setup_logger(__name__)


class BalanceService:
    @staticmethod
    async def recalculate_merchant_available_balance(db: AsyncSession, merchant_id: str, currency: str) -> Decimal:
        logger.info(f"Recalculating available balance for merchant {merchant_id}, currency {currency}")

        result = await db.execute(
            select(db_models.Account)
            .where(
                db_models.Account.merchant_id == merchant_id,
                db_models.Account.account_type == AccountType.MERCHANT_AVAILABLE,
                db_models.Account.currency == currency
            )
        )
        merchant_available_account = result.scalar_one_or_none()

        if not merchant_available_account:
            logger.warning(f"No MERCHANT_AVAILABLE account found for merchant {merchant_id}, currency {currency}")
            return Decimal("0.0000")

        ledger_result = await db.execute(
            select(func.coalesce(func.sum(db_models.LedgerTransaction.amount), 0))
            .where(
                db_models.LedgerTransaction.merchant_id == merchant_id,
                db_models.LedgerTransaction.currency == currency,
                db_models.LedgerTransaction.credit_account_id == merchant_available_account.id
            )
        )
        credits = ledger_result.scalar() or Decimal("0")

        debit_result = await db.execute(
            select(func.coalesce(func.sum(db_models.LedgerTransaction.amount), 0))
            .where(
                db_models.LedgerTransaction.merchant_id == merchant_id,
                db_models.LedgerTransaction.currency == currency,
                db_models.LedgerTransaction.debit_account_id == merchant_available_account.id
            )
        )
        debits = debit_result.scalar() or Decimal("0")

        calculated_balance = credits - debits
        logger.info(f"Calculated balance for merchant {merchant_id}: credits={credits}, debits={debits}, balance={calculated_balance}")

        if merchant_available_account.balance != calculated_balance:
            logger.warning(f"Balance mismatch for merchant {merchant_id}: stored={merchant_available_account.balance}, calculated={calculated_balance}")
            merchant_available_account.balance = calculated_balance
            await db.flush()

        return calculated_balance

    @staticmethod
    async def sync_merchant_account_balance(db: AsyncSession, merchant_id: str) -> None:
        logger.info(f"Syncing merchant account balance for {merchant_id}")

        merchant_result = await db.execute(
            select(db_models.MerchantAccount).where(db_models.MerchantAccount.merchant_id == merchant_id)
        )
        merchant = merchant_result.scalar_one_or_none()
        if not merchant:
            logger.warning(f"Merchant {merchant_id} not found for balance sync")
            return

        available_result = await db.execute(
            select(func.coalesce(func.sum(db_models.Account.balance), 0))
            .where(
                db_models.Account.merchant_id == merchant_id,
                db_models.Account.account_type == AccountType.MERCHANT_AVAILABLE
            )
        )
        available_sum = available_result.scalar() or Decimal("0")

        pending_result = await db.execute(
            select(func.coalesce(func.sum(db_models.Account.balance), 0))
            .where(
                db_models.Account.merchant_id == merchant_id,
                db_models.Account.account_type == AccountType.MERCHANT_PENDING
            )
        )
        pending_sum = pending_result.scalar() or Decimal("0")

        if merchant.available_balance != available_sum:
            logger.info(f"Updating merchant {merchant_id} available_balance: {merchant.available_balance} -> {available_sum}")
            merchant.available_balance = available_sum

        if merchant.pending_balance != pending_sum:
            logger.info(f"Updating merchant {merchant_id} pending_balance: {merchant.pending_balance} -> {pending_sum}")
            merchant.pending_balance = pending_sum

        await db.flush()
        logger.info(f"Balance sync complete for merchant {merchant_id}")

    @staticmethod
    async def get_charge_with_ledger(db: AsyncSession, charge_id: str):
        charge_result = await db.execute(select(db_models.Charge).where(db_models.Charge.id == charge_id))
        charge = charge_result.scalar_one_or_none()

        if not charge:
            return None

        ledger_result = await db.execute(
            select(db_models.LedgerTransaction)
            .where(db_models.LedgerTransaction.charge_id == charge_id)
            .order_by(db_models.LedgerTransaction.created_at)
        )
        ledger_entries = ledger_result.scalars().all()

        user_result = await db.execute(select(db_models.User).where(db_models.User.id == charge.user_id))
        user = user_result.scalar_one_or_none()

        return {
            "charge": charge,
            "ledger_entries": list(ledger_entries),
            "user": user
        }
