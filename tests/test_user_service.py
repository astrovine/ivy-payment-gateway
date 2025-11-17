import pytest

from app.models import db_models
from app.services.user_service import UserService
from app.utilities.exceptions import (
    UserAlreadyVerifiedError,
    InvalidCredentialsError,
    PasswordMismatchError,
    InvalidResetTokenError,
    ExpiredResetTokenError,
    PaymentGatewayException,
)

def test_create_user_account(db_session, test_new_user):
    user = UserService.create_user(db=db_session, user_data=test_new_user)
    assert user.email == test_new_user.email
    assert user.password != test_new_user.password
    assert user.is_active == True


def test_create_user_account_duplicate_error(db_session, test_new_user):
    UserService.create_user(db=db_session, user_data=test_new_user)
    with pytest.raises(PaymentGatewayException):
        UserService.create_user(db=db_session, user_data=test_new_user)


def test_verify_user_account(db_session, test_verify_user, test_new_user):
    user = UserService.create_user(db=db_session, user_data=test_new_user)
    verified_user = UserService.verify_user_account(db=db_session, current_user=user, verification_data=test_verify_user)
    assert verified_user.business_type.value == test_verify_user.business_type
    assert verified_user.business_name == test_verify_user.business_name
    assert verified_user.industry == test_verify_user.industry
    with pytest.raises(UserAlreadyVerifiedError):
        UserService.verify_user_account(db=db_session, current_user=user, verification_data=test_verify_user)


def test_update_user_account(db_session, test_new_user, test_update_user):
    user = UserService.create_user(db=db_session, user_data=test_new_user)
    updated_user = UserService.update_user_account(db=db_session, user_id=user.id, update_data=test_update_user)
    assert updated_user.name == user.name
    assert updated_user.email == user.email
    assert updated_user.country == user.country


def test_change_user_password_success(db_session, test_new_user):
    user = UserService.create_user(db=db_session, user_data=test_new_user)
    UserService.change_user_password(
        db=db_session,
        user=user,
        old_password="hashed_password",
        new_password="new_secure_password",
        confirm_password="new_secure_password",
    )
    assert user.password is not None and isinstance(user.password, str)


def test_change_user_password_wrong_old(db_session, test_new_user):
    user = UserService.create_user(db=db_session, user_data=test_new_user)
    with pytest.raises(InvalidCredentialsError):
        UserService.change_user_password(
            db=db_session,
            user=user,
            old_password="wrong_old",
            new_password="new_pw",
            confirm_password="new_pw",
        )


def test_change_user_password_mismatch(db_session, test_new_user):
    user = UserService.create_user(db=db_session, user_data=test_new_user)
    with pytest.raises(PasswordMismatchError):
        UserService.change_user_password(
            db=db_session,
            user=user,
            old_password="hashed_password",
            new_password="new_pw1",
            confirm_password="new_pw2",
        )



def test_request_password_reset_existing_user(db_session, test_new_user):
    user = UserService.create_user(db=db_session, user_data=test_new_user)
    res = UserService.request_password_reset(db=db_session, email=user.email)
    assert res is not None
    token, user_obj = res
    assert isinstance(token, str) and len(token) > 0
    assert user_obj.id == user.id
    assert user_obj.password_reset_token is not None
    assert user_obj.password_reset_expires is not None


def test_request_password_reset_nonexistent_user(db_session):
    res = UserService.request_password_reset(db=db_session, email="nope@example.com")
    assert res is None


def test_verify_reset_token_valid(db_session, test_new_user):
    user = UserService.create_user(db=db_session, user_data=test_new_user)
    token, _ = UserService.request_password_reset(db=db_session, email=user.email)  # type: ignore
    found = UserService.verify_reset_token(db=db_session, token=token)
    assert found.email == user.email


def test_verify_reset_token_invalid(db_session, test_new_user):
    user = UserService.create_user(db=db_session, user_data=test_new_user)
    UserService.request_password_reset(db=db_session, email=user.email)
    with pytest.raises(InvalidResetTokenError):
        UserService.verify_reset_token(db=db_session, token="completely_invalid_token")


def test_verify_reset_token_expired(db_session, test_new_user):
    user = UserService.create_user(db=db_session, user_data=test_new_user)
    token, user_obj = UserService.request_password_reset(db=db_session, email=user.email)  # type: ignore
    user_obj.password_reset_expires = user_obj.password_reset_expires.replace(year=2000)  # type: ignore
    db_session.flush()
    with pytest.raises(ExpiredResetTokenError):
        UserService.verify_reset_token(db=db_session, token=token)


def test_reset_password_success(db_session, test_new_user):
    user = UserService.create_user(db=db_session, user_data=test_new_user)
    token, _ = UserService.request_password_reset(db=db_session, email=user.email)  # type: ignore
    UserService.reset_password(db=db_session, token=token, new_password="brand_new_yeahh", confirm_password="brand_new_yeahh")
    refetched = UserService.get_user_by_id(db=db_session, user_id=user.id)
    assert refetched.password_reset_token is None
    assert refetched.password_reset_expires is None
    assert refetched is not None


def test_get_full_user_info_unverified(db_session, test_new_user):
    user = UserService.create_user(db=db_session, user_data=test_new_user)
    fetched = UserService.get_full_user_info(db=db_session, user_id=user.id)
    assert fetched.verified_info is None
    assert fetched is not None


def test_get_full_user_info_verified(db_session, test_new_user, test_verify_user):
    user = UserService.create_user(db=db_session, user_data=test_new_user)
    UserService.verify_user_account(db=db_session, current_user=user, verification_data=test_verify_user)
    fetched = UserService.get_full_user_info(db=db_session, user_id=user.id)
    assert fetched.verified_info.business_name == test_verify_user.business_name
    assert fetched is not None and fetched.verified_info is not None

def test_get_user_by_id_and_email(db_session, test_new_user):
    user = UserService.create_user(db=db_session, user_data=test_new_user)
    by_id = UserService.get_user_by_id(db_session, user_id=user.id)
    by_email = UserService.get_user_by_email(db_session, email=user.email)
    assert by_email is not None and by_email.email == user.email
    assert by_id is not None and by_id.id == user.id


def test_get_activity_logs_basic(db_session, test_new_user):
    user = UserService.create_user(db=db_session, user_data=test_new_user)
    log = db_models.AuditLog(
        user_id=user.id,
        merchant_id=None,
        action="login",
        resource_type="user",
        resource_id=str(user.id),
        ip_address="127.0.0.1",
        user_agent="pytest",
        changes=None,
        extra_data=None,
    )
    db_session.add(log)
    db_session.commit()

    logs = UserService.get_activity_logs(db=db_session, user=user)
    assert isinstance(logs, list)
    assert len(logs) == 1
    assert logs[0].action == "login"
