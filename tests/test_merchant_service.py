from decimal import Decimal
import pytest
from sqlalchemy.orm import Session
from app.services.merchant_service import MerchantService
from app.schemas import merchant as mer_schema
from app.models import db_models
from app.utilities.exceptions import DatabaseError


def test_create_merchant_account_success(db_session: Session):
    test_user = db_models.User(
        name="Random person idk",
        email="idk@example.com",
        password="hashed_password",
        country="Mars"
    )
    db_session.add(test_user)
    db_session.commit()
    db_session.refresh(test_user)

    create_data = mer_schema.MerchantAccountCreate(
        currency="NGN",
        settlement_schedule="daily"
    )

    new_merchant = MerchantService.create_merchant_account(
        db=db_session,
        data=create_data,
        user_id=test_user.id
    )

    assert new_merchant.user_id == test_user.id
    assert new_merchant.currency == "NGN"
    assert new_merchant.account_status == db_models.AccountStatus.active
    assert "merch_" in new_merchant.merchant_id

    limit_record = db_session.query(db_models.TransactionLimit).filter_by(merchant_id=new_merchant.merchant_id).first()
    assert limit_record is not None

    fee_record = db_session.query(db_models.FeeStructure).filter_by(merchant_id=new_merchant.merchant_id).first()
    assert fee_record is not None
    assert fee_record.percentage_fee == Decimal('0.0290')

    settings_record = db_session.query(db_models.MerchantSettings).filter_by(
        merchant_id=new_merchant.merchant_id).first()
    assert settings_record is not None
    assert settings_record.email_notifications == True
    assert new_merchant is not None

    pending_acct = db_session.query(db_models.Account).filter_by(
        merchant_id=new_merchant.merchant_id,
        account_type=db_models.AccountType.MERCHANT_PENDING
    ).first()
    assert pending_acct is not None
    assert pending_acct.balance == 0

    available_acct = db_session.query(db_models.Account).filter_by(
        merchant_id=new_merchant.merchant_id,
        account_type=db_models.AccountType.MERCHANT_AVAILABLE
    ).first()
    assert available_acct is not None
    assert available_acct.balance == 0


def test_create_merchant_account_fails_if_already_exists(db_session: Session, test_user):
    create_data = mer_schema.MerchantAccountCreate(currency="NGN", settlement_schedule="daily")
    MerchantService.create_merchant_account(db=db_session, data=create_data, user_id=test_user.id)

    with pytest.raises(DatabaseError, match="Merchant account already exists"):
        MerchantService.create_merchant_account(db=db_session, data=create_data, user_id=test_user.id)


def test_merchant_update_account(db_session: Session, test_user, test_update_data):
    create_data = mer_schema.MerchantAccountCreate(currency="NGN", settlement_schedule="daily")
    MerchantService.create_merchant_account(db=db_session, data=create_data, user_id=test_user.id)
    mer_up = MerchantService.update_merchant_account(db=db_session, data=test_update_data, user_id=test_user.id)
    assert mer_up.currency == "USD"
    assert mer_up.settlement_schedule == "monthly"


def test_create_merchant_api_key(db_session: Session, test_user, tes_api_key):
    create_data = mer_schema.MerchantAccountCreate(currency="NGN", settlement_schedule="daily")
    merchant = MerchantService.create_merchant_account(db=db_session, data=create_data, user_id=test_user.id)
    key = MerchantService.create_api_key(db=db_session, user_id=merchant.user_id, key_data=tes_api_key)
    assert key is not None
    assert key[0].key_prefix == 'pk_live_'
    assert key[0].api_key != key[1]
    assert key[0].name == 'API'
    assert key[0].key_type == 'publishable' and key[0].environment == 'live'
    assert key[0].is_active == True
    assert key[0].merchant_id == merchant.merchant_id

def test_update_merchant_key(db_session: Session, test_user, test_update_key, tes_api_key):
    create_data = mer_schema.MerchantAccountCreate(currency="NGN", settlement_schedule="daily")
    merchant = MerchantService.create_merchant_account(db=db_session, data=create_data, user_id=test_user.id)
    key = MerchantService.create_api_key(db=db_session, user_id=merchant.user_id, key_data=tes_api_key)
    updated_key = MerchantService.update_api_key(db=db_session, user_id=test_user.id, key_id=key[0].id, update_data=test_update_key)
    assert updated_key.name == 'Wanted to say something sarcastic'
    assert updated_key is not None

def test_revoked_merchant_key(db_session: Session, test_user, tes_api_key):
    create_data = mer_schema.MerchantAccountCreate(currency="NGN", settlement_schedule="daily")
    merchant = MerchantService.create_merchant_account(db=db_session, data=create_data, user_id=test_user.id)
    key = MerchantService.create_api_key(db=db_session, user_id=merchant.user_id, key_data=tes_api_key)
    revoked_key = MerchantService.revoke_api_key(db=db_session, user_id=test_user.id, key_id=key[0].id, reason='Jazz on a sunday evening')
    assert revoked_key.is_active == False
    assert revoked_key.revoke_reason == 'Jazz on a sunday evening'

def test_roll_merchant_key(db_session: Session, test_user, tes_api_key):
    create_data = mer_schema.MerchantAccountCreate(currency="NGN", settlement_schedule="daily")
    merchant = MerchantService.create_merchant_account(db=db_session, data=create_data, user_id=test_user.id)
    key = MerchantService.create_api_key(db=db_session, user_id=merchant.user_id, key_data=tes_api_key)
    rolled = MerchantService.roll_api_key(db=db_session, user_id=merchant.user_id, key_id=key[0].id)
    assert rolled[0].name == 'API (rolled)'
    assert rolled[0].key_type == 'publishable' and rolled[0].environment == 'live'
    assert rolled[0].is_active == True
    assert rolled is not None




