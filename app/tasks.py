from contextlib import contextmanager
from decimal import Decimal

from celery import shared_task
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.celery_worker import celery_app
from app.models import db_models
from app.models.db_models import TransactionType, AccountType
from app.utilities.exceptions import DatabaseError
from app.utilities.logger import setup_logger
from app.utilities.db_con import SessionLocal
import httpx

from app.services.webhook_service import WebhookService
from app.utilities.logger import setup_logger
from app.services.notification_service import NotificationService

logger = setup_logger(__name__)

FEE_RATE = Decimal("0.005")


@contextmanager
def session_scope():
    session: Session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        logger.error(f"Task DB Error: {e}", exc_info=True)
        session.rollback()
        raise
    finally:
        session.close()


@shared_task(name="app.tasks.process_charge_task", bind=True)
def process_charge_task(self, charge_id: str, payment_token: str = "tok_valid_success"):
    logger.info(f"Worker: Received charge {charge_id} with token {payment_token}")
    with session_scope() as db:
        charge = db.query(db_models.Charge).filter_by(id=charge_id).with_for_update().first()

        if not charge:
            logger.error(f"Worker: Charge {charge_id} not found. Task aborting.")
            return

        if charge.status != 'pending':
            logger.warning(f"Worker: Charge {charge_id} already processed. Status: {charge.status}. Task aborting.")
            return

        if payment_token == "tok_card_declined":
            charge.status = "failed"
            charge.failure_message = "Your card was declined."
            logger.warning(f"Task: Charge {charge_id} simulated FAILED (tok_card_declined).")

        elif payment_token == "tok_insufficient_funds":
            charge.status = "failed"
            charge.failure_message = "Insufficient funds."
            logger.warning(f"Task: Charge {charge_id} simulated FAILED (tok_insufficient_funds).")

        elif payment_token == "tok_valid_success":
            logger.info(f"Task: Charge {charge_id} simulated SUCCEEDED. Processing ledger.")

            merchant_account = db.query(db_models.MerchantAccount).filter_by(
                user_id=charge.user_id).with_for_update().first()
            if not merchant_account:
                raise DatabaseError("Merchant account not found for charge user")
            if merchant_account.currency != charge.currency:
                charge.status = 'failed'
                charge.failure_message = f"Currency mismatch: merchant uses {merchant_account.currency}"
                logger.warning(f"Charge {charge_id} failed due to currency mismatch: {charge.currency} vs {merchant_account.currency}")
                return

            system_holding_acct = db.query(db_models.Account).filter_by(
                account_type=AccountType.SYSTEM_HOLDING, currency=charge.currency
            ).with_for_update().first()
            if not system_holding_acct:
                system_holding_acct = db_models.Account(
                    account_type=AccountType.SYSTEM_HOLDING, currency=charge.currency, balance=0
                )
                db.add(system_holding_acct)
                db.flush()

            platform_revenue_acct = db.query(db_models.Account).filter_by(
                account_type=AccountType.PLATFORM_REVENUE, currency=charge.currency
            ).with_for_update().first()
            if not platform_revenue_acct:
                platform_revenue_acct = db_models.Account(
                    account_type=AccountType.PLATFORM_REVENUE, currency=charge.currency, balance=0
                )
                db.add(platform_revenue_acct)
                db.flush()

            merchant_pending_acct = db.query(db_models.Account).filter_by(
                merchant_id=merchant_account.merchant_id,
                account_type=AccountType.MERCHANT_PENDING
            ).with_for_update().first()
            if not merchant_pending_acct:
                merchant_pending_acct = db_models.Account(
                    merchant_id=merchant_account.merchant_id,
                    account_type=AccountType.MERCHANT_PENDING,
                    currency=charge.currency,
                    balance=0
                )
                db.add(merchant_pending_acct)
                db.flush()

            db.flush()

            total_amount = charge.amount
            fee_amount = total_amount * Decimal("0.02")
            net_amount = total_amount - fee_amount

            ledger_fee = db_models.LedgerTransaction(
                charge_id=charge.id,
                merchant_id=merchant_account.merchant_id,
                transaction_type=TransactionType.FEE,
                amount=fee_amount,
                currency=charge.currency,
                debit_account_id=system_holding_acct.id,
                credit_account_id=platform_revenue_acct.id
            )

            ledger_charge = db_models.LedgerTransaction(
                charge_id=charge.id,
                merchant_id=merchant_account.merchant_id,
                transaction_type=TransactionType.CHARGE,
                amount=net_amount,
                currency=charge.currency,
                debit_account_id=system_holding_acct.id,
                credit_account_id=merchant_pending_acct.id
            )

            db.add_all([ledger_fee, ledger_charge])
            platform_revenue_acct.balance += fee_amount
            merchant_pending_acct.balance += net_amount
            charge.status = 'succeeded'

            try:
                hooks = db.query(db_models.WebhookEndpoint).filter_by(merchant_id=merchant_account.merchant_id, enabled=True).all()
                for hook in hooks:
                    payload = {
                        "event": "charge.succeeded",
                        "charge_id": charge.id,
                        "amount": str(charge.amount),
                        "currency": charge.currency,
                        "merchant_id": merchant_account.merchant_id
                    }
                    delivery = WebhookService.record_delivery(db=db, webhook_id=hook.id, event="charge.succeeded", payload=payload)
                    celery_app.send_task("app.tasks.process_webhook_delivery", args=(delivery.id,))
            except Exception as e:
                logger.exception(f"Error creating webhook deliveries for charge {charge.id}: {e}")

            # create notification for merchant about charge
            try:
                NotificationService.create_notification(db=db, merchant_id=merchant_account.merchant_id, user_id=charge.user_id, type='charge.succeeded', message=f"Charge succeeded: {charge.amount} {charge.currency}", data=str({"charge_id": charge.id}))
            except Exception:
                logger.exception("Failed to create charge succeeded notification")

            logger.info(f"Worker: Charge {charge_id} ledger logic complete.")

        else:
            charge.status = "failed"
            charge.failure_message = "Invalid payment token provided."
            logger.error(f"Task: Charge {charge_id} failed (Invalid payment token).")


@celery_app.task(name="app.tasks.settle_pending_funds_task")
def settle_pending_funds_task():
    logger.info("Settlement task started...")
    with session_scope() as db:
        try:
            merchants = db.query(db_models.MerchantAccount).all()

            for merchant in merchants:
                pending_acct = db.query(db_models.Account).filter_by(
                    merchant_id=merchant.merchant_id,
                    account_type=AccountType.MERCHANT_PENDING
                ).with_for_update().first()

                available_acct = db.query(db_models.Account).filter_by(
                    merchant_id=merchant.merchant_id,
                    account_type=AccountType.MERCHANT_AVAILABLE
                ).with_for_update().first()
                amount_to_settle = pending_acct.balance

                if amount_to_settle > 0:
                    logger.info(f"Settling {amount_to_settle} {merchant.currency} for merchant {merchant.merchant_id}")

                    debit_entry = db_models.LedgerTransaction(
                        merchant_id=merchant.merchant_id,
                        transaction_type=TransactionType.CHARGE,
                        amount=amount_to_settle,
                        currency=merchant.currency,
                        debit_account_id=pending_acct.id,
                        credit_account_id=available_acct.id
                    )
                    db.add(debit_entry)

                    pending_acct.balance -= amount_to_settle
                    available_acct.balance += amount_to_settle
                    merchant.pending_balance -= amount_to_settle
                    merchant.available_balance += amount_to_settle


                    audit = db_models.AuditLog(
                        user_id=merchant.user_id,
                        merchant_id=merchant.merchant_id,
                        action="FUNDS_SETTLED",
                        resource_type="MERCHANT_ACCOUNT",
                        resource_id=str(merchant.merchant_id),
                        extra_data=str({
                            "amount_settled": str(amount_to_settle),
                            "currency": merchant.currency
                        })
                    )
                    db.add(audit)
                    try:
                        NotificationService.create_notification(db=db, merchant_id=merchant.merchant_id, user_id=merchant.user_id, type='settlement.succeeded', message=f"Settlement completed: {amount_to_settle} {merchant.currency}", data=str({"amount": str(amount_to_settle)}))
                    except Exception:
                        logger.exception("Failed to create settlement notification")
                    try:
                        hooks = db.query(db_models.WebhookEndpoint).filter_by(merchant_id=merchant.merchant_id, enabled=True).all()
                        for hook in hooks:
                            payload = {
                                "event": "settlement.succeeded",
                                "merchant_id": merchant.merchant_id,
                                "amount": str(amount_to_settle),
                                "currency": merchant.currency
                            }
                            delivery = WebhookService.record_delivery(db=db, webhook_id=hook.id, event="settlement.succeeded", payload=payload)
                            celery_app.send_task("app.tasks.process_webhook_delivery", args=(delivery.id,))
                    except Exception as e:
                        logger.exception(f"Error creating webhook delivery for settlement {merchant.merchant_id}: {e}")

            logger.info("Settlement task finished successfully.")

        except Exception as e:
            logger.error(f"Settlement task failed: {e}", exc_info=True)


@celery_app.task(name="app.tasks.process_payout_task")
def process_payout_task(payout_id: str):
    with session_scope() as db:
        payout = db.query(db_models.Payout).filter_by(id=payout_id).with_for_update().first()
        if not payout:
            logger.error(f"Payout {payout_id} not found.")
            return

        current_status = getattr(payout, 'status', None)
        pending_match = current_status == db_models.PayoutStatus.PENDING or current_status == getattr(db_models.PayoutStatus.PENDING, 'name', None) or current_status == getattr(db_models.PayoutStatus.PENDING, 'value', None)
        if not pending_match:
            logger.warning(f"Payout {payout_id} is already being processed or is complete.")
            return
        existing_ledgers = db.query(db_models.LedgerTransaction).filter(db_models.LedgerTransaction.payout_id == payout.id).all()
        try:
            if existing_ledgers:
                payout.status = db_models.PayoutStatus.SUCCEEDED
                payout.processed_at = func.now()
                db.add(payout)
                audit = db_models.AuditLog(
                    user_id=payout.merchant.user_id if payout.merchant else None,
                    merchant_id=payout.merchant_id,
                    action="PAYOUT_PROCESSED",
                    resource_type="PAYOUT",
                    resource_id=str(payout.id),
                    extra_data=str({"amount": str(payout.amount), "currency": payout.currency})
                )
                db.add(audit)
                db.commit()
                logger.info(f"Finalized payout {payout_id} (reservation path)")
                try:
                    NotificationService.create_notification(db=db, merchant_id=payout.merchant_id, user_id=payout.merchant.user_id if payout.merchant else None, type='payout.succeeded', message=f"Payout succeeded: {payout.amount} {payout.currency}", data=str({"payout_id": payout.id}))
                except Exception:
                    logger.exception("Failed to create payout succeeded notification (reservation path)")
                return
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
                logger.error(f"Missing ledger accounts for payout {payout_id} (Currency: {payout.currency})")
                payout.status = db_models.PayoutStatus.FAILED
                payout.failure_reason = "Internal platform accounting error."
                db.add(payout)
                db.commit()
                return

            if available_acct.balance < payout.amount:
                logger.warning(f"Insufficient funds for payout {payout_id}. Found {available_acct.balance} but needed {payout.amount}")
                payout.status = db_models.PayoutStatus.FAILED
                payout.failure_reason = "Insufficient funds at time of processing."
                db.add(payout)
                db.commit()
                return

            fee_amount = (payout.amount * FEE_RATE).quantize(Decimal("0.0001"))

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
                    description=f"Payout fee for {payout.id}",
                    amount=fee_amount,
                    transaction_type=db_models.TransactionType.FEE,
                    currency=payout.currency,
                    debit_account_id=available_acct.id,
                    credit_account_id=platform_revenue_acct.id
                )
                db.add(fee_ledger)

            available_acct.balance -= (payout.amount + (fee_amount if fee_amount else Decimal('0')))
            payable_acct.balance += payout.amount
            platform_revenue_acct.balance += (fee_amount if fee_amount else Decimal('0'))
            if payout.merchant:
                payout.merchant.available_balance -= (payout.amount + (fee_amount if fee_amount else Decimal('0')))

            payout.status = db_models.PayoutStatus.SUCCEEDED
            payout.processed_at = func.now()
            audit = db_models.AuditLog(
                user_id=payout.merchant.user_id if payout.merchant else None,
                merchant_id=payout.merchant_id,
                action="PAYOUT_PROCESSED",
                resource_type="PAYOUT",
                resource_id=str(payout.id),
                extra_data=str({"amount": str(payout.amount), "fee": str(fee_amount), "currency": payout.currency})
            )
            db.add(audit)
            db.commit()
            try:
                hooks = db.query(db_models.WebhookEndpoint).filter_by(merchant_id=payout.merchant_id, enabled=True).all()
                for hook in hooks:
                    payload = {
                        "event": "payout.succeeded",
                        "payout_id": payout.id,
                        "amount": str(payout.amount),
                        "currency": payout.currency,
                        "merchant_id": payout.merchant_id
                    }
                    delivery = WebhookService.record_delivery(db=db, webhook_id=hook.id, event="payout.succeeded", payload=payload)
                    celery_app.send_task("app.tasks.process_webhook_delivery", args=(delivery.id,))
            except Exception as e:
                logger.exception(f"Error creating webhook deliveries for payout {payout.id}: {e}")

            logger.info(f"Successfully processed payout {payout_id} (fallback path). fee={fee_amount}")
            try:
                NotificationService.create_notification(db=db, merchant_id=payout.merchant_id, user_id=payout.merchant.user_id if payout.merchant else None, type='payout.succeeded', message=f"Payout succeeded: {payout.amount} {payout.currency}", data=str({"payout_id": payout.id, "fee": str(fee_amount)}))
            except Exception:
                logger.exception("Failed to create payout succeeded notification (fallback path)")

        except Exception as e:
            logger.error(f"Error processing payout {payout_id}: {e}", exc_info=True)
            db.rollback()
            try:
                payout.status = db_models.PayoutStatus.FAILED
                payout.failure_reason = "Processing error"
                db.add(payout)
                db.commit()
                try:
                    NotificationService.create_notification(db=db, merchant_id=payout.merchant_id, user_id=payout.merchant.user_id if payout.merchant else None, type='payout.failed', message=f"Payout failed: {payout.amount} {payout.currency}", data=str({"payout_id": payout.id, "reason": payout.failure_reason}))
                except Exception:
                    logger.exception("Failed to create payout failed notification")
            except Exception:
                db.rollback()
            return


@celery_app.task(name="app.tasks.process_webhook_delivery")
def process_webhook_delivery(delivery_id: int):
    logger.info(f"Processing webhook delivery {delivery_id}")
    with session_scope() as db:
        try:
            delivery = db.query(db_models.WebhookDelivery).filter_by(id=delivery_id).with_for_update().first()
            if not delivery:
                logger.error(f"Delivery {delivery_id} not found")
                return

            webhook = db.query(db_models.WebhookEndpoint).filter_by(id=delivery.webhook_id).first()
            if not webhook or not webhook.enabled:
                logger.warning(f"Webhook for delivery {delivery_id} is disabled or missing")
                delivery.attempts = (delivery.attempts or 0) + 1
                delivery.status = 'failed'
                delivery.last_attempt_at = func.now()
                db.add(delivery)
                return

            payload = None
            try:
                import json
                try:
                    payload = json.loads(delivery.payload)
                except Exception:
                    payload = delivery.payload

                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(webhook.url, json=payload)
                http_status = resp.status_code
                response_body = resp.text
                delivery.attempts = (delivery.attempts or 0) + 1
                delivery.http_status = http_status
                delivery.response_body = response_body
                delivery.status = 'success' if http_status < 400 else 'failed'
                delivery.last_attempt_at = func.now()
                db.add(delivery)

                note_msg = f"Webhook event '{delivery.event}' delivery {delivery.status} (http {http_status})"
                note = db_models.Notification(
                    merchant_id=webhook.merchant_id,
                    user_id=None,
                    type='webhook.delivery',
                    message=note_msg,
                    data=str({"delivery_id": delivery.id, "http_status": http_status}),
                    is_read=False
                )
                db.add(note)
                db.commit()
                logger.info(f"Processed delivery {delivery_id}: status={delivery.status} http={http_status}")

            except Exception as e:
                logger.exception(f"Error sending webhook delivery {delivery_id}: {e}")
                delivery.attempts = (delivery.attempts or 0) + 1
                delivery.status = 'failed'
                delivery.response_body = str(e)
                delivery.last_attempt_at = func.now()
                db.add(delivery)

                note_msg = f"Webhook event '{delivery.event}' delivery failed: {str(e)}"
                note = db_models.Notification(
                    merchant_id=webhook.merchant_id if webhook else None,
                    user_id=None,
                    type='webhook.delivery',
                    message=note_msg,
                    data=str({"delivery_id": delivery.id}),
                    is_read=False
                )
                db.add(note)
                db.commit()

        except Exception as ex:
            logger.exception(f"Unexpected error processing webhook delivery {delivery_id}: {ex}")
            try:
                db.rollback()
            except Exception:
                pass
