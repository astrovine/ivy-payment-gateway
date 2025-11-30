import os
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")

import uuid
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import db_models
from app.schemas import account as ac
from app.schemas import api_key as api
from app.schemas import charges
from app.schemas import merchant as mer
from app.utilities.db_con import Base

TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

import app.tasks as tasks_module

tasks_module.SessionLocal = TestingSessionLocal


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user(db_session):
    user = db_models.User(
        name="Random person idk",
        email="idk@example.com",
        password="hashed_password",
        country="Mars"
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user

@pytest.fixture
def test_new_user(db_session):
    user = db_models.User(
        name="dhee",
        email="dhee@example.com",
        password="hashed_password",
        country="London"
    )
    return user

@pytest.fixture
def test_verify_user(db_session):
    data = ac.UserVer(
        industry='Finance',
        staff_size=1,
        business_name='Bank of America',
        business_email='bofa@gmail.com',
        business_type= 'Registered',
        business_website="https://www.bankofamerica.com/", # type: ignore
        business_description='A great place to work!',
        location='London',
        support_email='bofa2@gmail.com', # type: ignore
        phone_number='0123456789',
        support_phone='0123456789',
        bank_account_name='Bank of America Uk',
        bank_account_number= '123456789',
        bank_name='Bank of America'
    )
    return data

@pytest.fixture
def test_update_data(db_session):
    merchant_update = mer.MerchantAccountUpdate(
        currency="USD",
        settlement_schedule="monthly"
    )
    return merchant_update

@pytest.fixture
def tes_api_key(db_session):
    api_key = api.APIKeyCreate(
        name="API",
        key_type='publishable',
        environment='live'
    )
    return api_key

@pytest.fixture
def test_update_key(db_session):
    api_key_name = api.APIKeyUpdate(
        name='Wanted to say something sarcastic'
    )
    return api_key_name

@pytest.fixture
def test_update_user(db_session):
    data = ac.UserUpdate(
        name="Frank ocean",
        email="nights@gmail.com", # type: ignore
        country='SF'
    )
    return data

@pytest.fixture
def test_new_charge(db_session):
    charge = charges.ChargeCreate(
        amount=Decimal('100.00'),
        currency="USD",
        description="A test charge",
        idempotency_key=str(uuid.uuid4())
    )
    return charge
