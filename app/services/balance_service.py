from decimal import Decimal
from sqlalchemy.orm import Session
from ..models import db_models
from ..models.db_models import AccountType
from ..utilities.logger import setup_logger

logger = setup_logger(__name__)


class BalanceService:
    @staticmethod
    def recalculate_merchant_balance(db: Session, merchant_id: str):
        """
        Recalculate and update merchant balances based on ledger transactions
        """
        try:
            logger.info(f"Recalculating balances for merchant {merchant_id}")

            merchant_account = db.query(db_models.MerchantAccount).filter_by(
                merchant_id=merchant_id
            ).first()

            if not merchant_account:
                logger.error(f"Merchant account {merchant_id} not found")
                return

            pending_account = db.query(db_models.Account).filter_by(
                merchant_id=merchant_id,
                account_type=AccountType.MERCHANT_PENDING
            ).first()

            available_account = db.query(db_models.Account).filter_by(
                merchant_id=merchant_id,
                account_type=AccountType.MERCHANT_AVAILABLE
            ).first()

            if pending_account:
                pending_credits = db.query(db_models.LedgerTransaction).filter(
                    db_models.LedgerTransaction.merchant_id == merchant_id,
                    db_models.LedgerTransaction.credit_account_id == pending_account.id
                ).all()

                pending_debits = db.query(db_models.LedgerTransaction).filter(
                    db_models.LedgerTransaction.merchant_id == merchant_id,
                    db_models.LedgerTransaction.debit_account_id == pending_account.id
                ).all()

                total_credits = sum(Decimal(str(t.amount)) for t in pending_credits)
                total_debits = sum(Decimal(str(t.amount)) for t in pending_debits)

                pending_account.balance = total_credits - total_debits
                merchant_account.pending_balance = pending_account.balance

                logger.info(f"Merchant {merchant_id} pending balance recalculated: {pending_account.balance}")

            if available_account:
                available_credits = db.query(db_models.LedgerTransaction).filter(
                    db_models.LedgerTransaction.merchant_id == merchant_id,
                    db_models.LedgerTransaction.credit_account_id == available_account.id
                ).all()

                available_debits = db.query(db_models.LedgerTransaction).filter(
                    db_models.LedgerTransaction.merchant_id == merchant_id,
                    db_models.LedgerTransaction.debit_account_id == available_account.id
                ).all()

                total_credits = sum(Decimal(str(t.amount)) for t in available_credits)
                total_debits = sum(Decimal(str(t.amount)) for t in available_debits)

                available_account.balance = total_credits - total_debits
                merchant_account.available_balance = available_account.balance

                logger.info(f"Merchant {merchant_id} available balance recalculated: {available_account.balance}")

            db.commit()
            logger.info(f"Balance recalculation complete for merchant {merchant_id}")

        except Exception as e:
            db.rollback()
            logger.error(f"Error recalculating balance for merchant {merchant_id}: {e}", exc_info=True)
            raise

    @staticmethod
    def sync_balances_from_charges(db: Session, merchant_id: str):
        """
        Sync merchant balances based on actual charge statuses
        """
        try:
            logger.info(f"Syncing balances from charges for merchant {merchant_id}")

            merchant_account = db.query(db_models.MerchantAccount).filter_by(
                merchant_id=merchant_id
            ).with_for_update().first()

            if not merchant_account:
                logger.error(f"Merchant account {merchant_id} not found")
                return

            user = db.query(db_models.User).filter_by(id=merchant_account.user_id).first()
            if not user:
                logger.error(f"User not found for merchant {merchant_id}")
                return

            succeeded_charges = db.query(db_models.Charge).filter(
                db_models.Charge.user_id == user.id,
                db_models.Charge.status == 'succeeded'
            ).all()

            total_amount = sum(Decimal(str(c.amount)) for c in succeeded_charges)
            fee_amount = total_amount * Decimal("0.02")
            net_amount = total_amount - fee_amount

            merchant_account.pending_balance = net_amount
            merchant_account.available_balance = Decimal("0.00")

            db.commit()

            logger.info(f"Balance sync complete for merchant {merchant_id}: pending={net_amount}, available=0.00")

        except Exception as e:
            db.rollback()
            logger.error(f"Error syncing balances for merchant {merchant_id}: {e}", exc_info=True)
            raise

