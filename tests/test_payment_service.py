from decimal import Decimal

from app.models.db_models import Charge, LedgerTransaction
from app.schemas import merchant as mer_schema
from app.services.merchant_service import MerchantService
from app.services.payment_service import ChargeService
from app.services.user_service import UserService


def test_create_new_charge(db_session, test_new_charge, test_new_user):
    user = UserService.create_user(db=db_session,user_data=test_new_user)
    create_data = mer_schema.MerchantAccountCreate(currency="NGN", settlement_schedule="daily")
    MerchantService.create_merchant_account(db=db_session, data=create_data, user_id=user.id)
    count_before = db_session.query(Charge).count()
    new_charge = ChargeService.create_charge(db=db_session,charge_data=test_new_charge, user=user)
    charge_db = db_session.query(Charge).filter_by(user_id=user.id).first()
    ledger = db_session.query(LedgerTransaction).filter_by(charge_id=new_charge.id).first()
    count_after = db_session.query(Charge).count()
    assert charge_db.status == 'succeeded'
    assert ledger.amount == Decimal('100')
    assert ledger.transaction_type.value == 'CHARGE'
    assert charge_db.idempotency_key == new_charge.idempotency_key
    assert count_after == count_before + 1
    assert charge_db.idempotency_key == new_charge.idempotency_key
    assert charge_db and ledger is not None
