from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.security.oauth2 import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth

from ..models import db_models
from ..schemas import account as user_schema
from ..schemas import password as password_schema
from ..schemas import token
from ..services.email_service import EmailService
from ..services.user_service import UserService
from ..utilities import Oauth2
from ..utilities import Oauth2 as au
from ..utilities import db_con
from ..utilities.config import settings
from ..utilities.db_con import get_db
from ..utilities.exceptions import (
    DuplicateEmailError,
    UserCreationError,
    UserAlreadyVerifiedError,
    VerificationError,
    ExpiredResetTokenError,
    InvalidResetTokenError,
    PasswordMismatchError,
)
from ..utilities.logger import log_user_action, log_security_event, setup_logger
from ..utilities.utils import verify_password

logger = setup_logger(__name__)
router = APIRouter(prefix="/api/v1", tags=["Authentication"])

oauth = OAuth()
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    authorize_params=None,
    access_token_params=None,
    api_base_url='https://www.googleapis.com/oauth2/v1/',
    userinfo_endpoint='https://www.googleapis.com/oauth2/v1/userinfo?alt=json',
    client_kwargs={'scope': 'openid email profile'},
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
)

oauth.register(
    name='github',
    client_id=settings.GITHUB_CLIENT_ID,
    client_secret=settings.GITHUB_CLIENT_SECRET,
    access_token_params=None,
    authorize_params=None,
    api_base_url='https://api.github.com/',
    authorize_url='https://github.com/login/oauth/authorize',
    access_token_url='https://github.com/login/oauth/access_token',
    userinfo_endpoint='https://api.github.com/user',
    client_kwargs={'scope': 'user:email read:user'},
)

@router.post("/auth/register", response_model=user_schema.UserRes, status_code=status.HTTP_201_CREATED)
async def create_account(user_data: user_schema.UserCreate, request: Request, db: Session = Depends(get_db)):
    try:
        ip_address = request.client.host if request.client else "unknown"
        logger.info(f"New user registration attempt for email: {user_data.email}")
        new_user = UserService.create_user(db=db, user_data=user_data)
        log_user_action(
            db=db,
            user_id=new_user.id,
            action="USER_REGISTERED",
            resource_type="USER",
            resource_id=str(new_user.id),
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            extra_data={"email": new_user.email, "country": user_data.country}
        )
        db.commit()
        logger.info(f"User {new_user.id} registered successfully: {new_user.email}")
        return new_user
    except DuplicateEmailError:
        db.rollback()
        logger.warning(f"Registration failed: Email already exists - {user_data.email}")
        log_security_event("DUPLICATE_EMAIL_REGISTRATION", {"email": user_data.email})
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    except UserCreationError as e:
        db.rollback()
        logger.error(f"User creation error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post("/auth/login", response_model=token.LoginResponse)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), request: Request = None,
                db: Session = Depends(db_con.get_db)):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"Login attempt for email: {form_data.username} from IP: {ip_address}")
    user = db.query(db_models.User).filter_by(email=form_data.username).first()
    if not user:
        logger.warning(f"Failed login attempt - User not found for email: {form_data.username} from IP: {ip_address}")
        log_security_event(
            "FAILED_LOGIN_ATTEMPT",
            {"email": form_data.username, "ip_address": ip_address, "reason": "user_not_found"},
            severity="WARNING"
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    logger.info(f"User found: {user.id}, attempting password verification")
    logger.info(f"Password hash starts with: {user.password[:20] if user.password else 'None'}...")
    password_valid = verify_password(form_data.password, user.password)
    logger.info(f"Password verification result: {password_valid}")
    if not password_valid:
        logger.warning(f"Failed login attempt - Invalid password for email: {form_data.username} from IP: {ip_address}")
        log_security_event(
            "FAILED_LOGIN_ATTEMPT",
            {"email": form_data.username, "ip_address": ip_address, "reason": "invalid_password"},
            severity="WARNING"
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    access_token = Oauth2.create_access_token(data={"sub": str(user.id)})
    refresh_token = au.create_refresh_token(data={"sub": str(user.id)}, db=db)
    merchant_id = user.merchant_info.merchant_id if hasattr(user, 'merchant_info') and user.merchant_info else None
    log_user_action(
        db=db,
        user_id=user.id,
        action="USER_LOGIN",
        resource_type="USER",
        resource_id=str(user.id),
        merchant_id=merchant_id,
        ip_address=ip_address,
        user_agent=request.headers.get("user-agent") if request else None,
        extra_data={"email": user.email, "login_time": datetime.now(timezone.utc).isoformat()}
    )
    db.commit()
    logger.info(f"User {user.id} ({user.email}) logged in successfully from IP: {ip_address}")
    is_verified = user.verified_info is not None
    has_merchant = user.merchant_info is not None
    if not is_verified:
        onboarding_stage = "account_created"
    elif not has_merchant:
        onboarding_stage = "verified"
    else:
        onboarding_stage = "active"
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "country": user.country,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "is_verified": is_verified,
            "has_merchant_account": has_merchant,
            "onboarding_stage": onboarding_stage
        }
    }


@router.get("/auth/me", response_model=user_schema.UserDetailsRes)
async def get_current_user_details(current_user: db_models.User = Depends(au.get_current_user)):
    verified = current_user.verified_info
    return {
        "name": current_user.name,
        "email": current_user.email,
        "country": current_user.country,
        "verified_info": verified
    }


@router.post("/auth/refresh-token", response_model=token.Token)
async def refresh_access_token(
        request_body: token.RefreshTokenRequest,
        request: Request,
        db: Session = Depends(db_con.get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    ip_address = request.client.host if request else "unknown"
    try:
        refresh_token = request_body.refresh_token
        logger.info(f"Refresh token request from IP: {ip_address}")
        payload = Oauth2.verify_refresh_token(refresh_token, credentials_exception)
        stored_token = db.query(db_models.RefreshToken).filter_by(refresh_token=refresh_token).first()
        if not stored_token or stored_token.revoked:
            logger.warning(f"Attempted use of invalid/revoked refresh token from IP: {ip_address}")
            log_security_event(
                "INVALID_REFRESH_TOKEN_USED",
                {"ip_address": ip_address, "reason": "revoked or not found"},
                severity="WARNING"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token is invalid or has been revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if stored_token.expires_at < datetime.now(timezone.utc):
            logger.warning(f"Attempted use of expired refresh token from IP: {ip_address}")
            log_security_event(
                "EXPIRED_REFRESH_TOKEN_USED",
                {"ip_address": ip_address},
                severity="WARNING"
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        stored_token.revoked = True
        db.commit()
        user_id = payload.id
        new_access_token = Oauth2.create_access_token(data={"sub": user_id})
        new_refresh_token = Oauth2.create_refresh_token(data={"sub": user_id}, db=db)
        log_user_action(
            db=db,
            user_id=int(user_id),
            action="TOKEN_REFRESHED",
            resource_type="REFRESH_TOKEN",
            resource_id=refresh_token[:16],
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            extra_data={"refreshed_at": datetime.now(timezone.utc).isoformat()}
        )
        db.commit()
        logger.info(f"Access token refreshed successfully for user {user_id}")
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error in refresh_access_token: {e}", exc_info=True)
        log_security_event("REFRESH_TOKEN_ERROR", {"error": str(e), "ip_address": ip_address}, severity="ERROR")
        raise credentials_exception


@router.post('/auth/verify', response_model=user_schema.UserVerifiedInfoRes, status_code=status.HTTP_201_CREATED)
async def verify_user_account(verification_data: user_schema.UserVer, request: Request, db: Session = Depends(get_db),
                              current_user: db_models.User = Depends(au.get_current_user)):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"User {current_user.id} ({current_user.email}) initiated account verification from {ip_address}")
    try:
        verified_user = UserService.verify_user_account(
            db=db,
            current_user=current_user,
            verification_data=verification_data
        )
        log_user_action(
            db=db,
            user_id=current_user.id,
            action="USER_ACCOUNT_VERIFIED",
            resource_type="USER_VERIFIED",
            resource_id=str(current_user.id),
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent") if request else None,
            extra_data={
                "email": current_user.email,
                "business_type": verification_data.business_type,
                "verified_at": datetime.now(timezone.utc).isoformat()
            }
        )
        db.commit()
        logger.info(f"User {current_user.id} account verified successfully")
        return verified_user
    except UserAlreadyVerifiedError:
        db.rollback()
        logger.warning(f"User {current_user.id} attempted to verify already verified account from {ip_address}")
        log_security_event(
            "DUPLICATE_VERIFICATION_ATTEMPT",
            {"user_id": current_user.id, "email": current_user.email, "ip_address": ip_address},
            severity="INFO"
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already verified")
    except VerificationError as e:
        db.rollback()
        logger.error(f"Verification error for user {current_user.id}: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))


@router.post(
    '/auth/forgot-password',
    response_model=password_schema.ForgotPasswordResponse,
    status_code=status.HTTP_200_OK
)
async def forgot_password(
        data: password_schema.ForgotPasswordRequest,
        request: Request,
        db: Session = Depends(get_db)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"Password reset requested for email: {data.email} from IP: {ip_address}")
    try:
        result = UserService.request_password_reset(db=db, email=data.email)
        if result:
            reset_token, user = result
            email_sent = EmailService.send_password_reset_email(
                email=user.email,
                reset_token=reset_token,
                user_name=user.name
            )
            if email_sent:
                logger.info(f"Password reset email sent successfully to {user.email}")
                log_user_action(
                    db=db,
                    user_id=user.id,
                    action="PASSWORD_RESET_REQUESTED",
                    resource_type="USER",
                    resource_id=str(user.id),
                    ip_address=ip_address,
                    user_agent=request.headers.get("user-agent") if request else None,
                    extra_data={"email": user.email}
                )
                db.commit()
            else:
                logger.error(f"Failed to send password reset email to {user.email}")
        return password_schema.ForgotPasswordResponse(
            message="If the email exists, a password reset link has been sent"
        )
    except Exception as e:
        logger.error(f"Error in forgot_password for {data.email}: {str(e)}", exc_info=True)
        return password_schema.ForgotPasswordResponse(
            message="If the email exists, a password reset link has been sent"
        )


@router.post(
    '/auth/reset-password',
    response_model=password_schema.ResetPasswordResponse,
    status_code=status.HTTP_200_OK
)
async def reset_password(
        data: password_schema.ResetPasswordRequest,
        request: Request,
        db: Session = Depends(get_db)
):
    ip_address = request.client.host if request and request.client else "unknown"
    logger.info(f"Password reset attempt from IP: {ip_address}")
    try:
        UserService.reset_password(
            db=db,
            token=data.token,
            new_password=data.new_password,
            confirm_password=data.confirm_password
        )
        logger.info(f"Password successfully reset from IP: {ip_address}")
        log_security_event(
            event_type="PASSWORD_RESET_COMPLETED",
            details={"ip_address": ip_address},
            severity="INFO"
        )
        return password_schema.ResetPasswordResponse(
            message="Password has been reset successfully. You can now log in with your new password."
        )
    except PasswordMismatchError:
        logger.warning(f"Password mismatch in reset attempt from IP: {ip_address}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match"
        )
    except InvalidResetTokenError:
        logger.warning(f"Invalid reset token attempted from IP: {ip_address}")
        log_security_event(
            event_type="INVALID_RESET_TOKEN_USED",
            details={"ip_address": ip_address},
            severity="WARNING"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired password reset token"
        )
    except ExpiredResetTokenError:
        logger.warning(f"Expired reset token attempted from IP: {ip_address}")
        log_security_event(
            event_type="EXPIRED_RESET_TOKEN_USED",
            details={"ip_address": ip_address},
            severity="WARNING"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset token has expired. Please request a new one."
        )
    except Exception as e:
        logger.error(f"Unexpected error in reset_password: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password. Please try again."
        )


@router.get("/auth/google/login")
async def google_login(request: Request):
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/auth/google/callback")
async def google_callback(
        request: Request,
        db: Session = Depends(get_db)
):
    try:
        token = await oauth.google.authorize_access_token(request)
    except Exception as e:
        logger.error(f"Google OAuth Error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Failed to get token from Google")
    user_info = await oauth.google.get('userinfo', token=token)
    user_info_data = user_info.json()
    email = user_info_data.get("email")
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email not found in Google response")
    user = UserService.find_or_create_by_oauth(db, user_info_data)
    if not user:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create user")
    access_token = Oauth2.create_access_token(data={"sub": str(user.id)})
    refresh_token = au.create_refresh_token(data={"sub": str(user.id)}, db=db)
    return RedirectResponse(
        url=f"http://ivypayments.ddns.net:5173/auth/callback?access_token={access_token}&refresh_token={refresh_token}"
    )


@router.get("/auth/github/login")
async def github_login(request: Request):
    redirect_uri = "http://ivypayments.ddns.net:8000/api/v1/auth/github/callback"
    return await oauth.github.authorize_redirect(request, redirect_uri)


@router.get("/auth/github/callback")
async def github_callback(
        request: Request,
        db: Session = Depends(get_db)
):
    try:
        token = await oauth.github.authorize_access_token(request)
    except Exception as e:
        logger.error(f"GitHub OAuth Error: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Failed to get token from GitHub")

    user_info = await oauth.github.get('user', token=token)
    user_info_data = user_info.json()
    email = user_info_data.get("email")

    if not email:
        try:
            emails = await oauth.github.get('user/emails', token=token)
            email_data = emails.json()
            primary_email = next((e['email'] for e in email_data if e['primary']), None)
            if not primary_email:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail="No primary email found on GitHub account.")
            email = primary_email
            user_info_data['email'] = email
        except Exception as e:
            logger.error(f"GitHub email lookup failed: {e}", exc_info=True)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Could not retrieve email from GitHub.")

    if not user_info_data.get("name"):
        user_info_data["name"] = user_info_data.get("login", "GitHub User")

    user = UserService.find_or_create_by_oauth(db, user_info_data)
    if not user:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not create user")

    access_token = Oauth2.create_access_token(data={"sub": str(user.id)})
    refresh_token = au.create_refresh_token(data={"sub": str(user.id)}, db=db)
    return RedirectResponse(
        url=f"http://ivypayments.ddns.net:5173/auth/callback?access_token={access_token}&refresh_token={refresh_token}"
    )