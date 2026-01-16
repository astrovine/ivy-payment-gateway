from datetime import datetime, timedelta, timezone
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, APIKeyHeader
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .db_con import get_db
from ..models import db_models
from ..schemas import token as tk
from ..utilities.utils import verify_password
from .logger import log_user_action, log_security_event, setup_logger

logger = setup_logger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    user_id = data.get("sub")
    logger.info(f"Access token created for user {user_id}, expires at {expire}")
    return encoded_jwt


async def create_refresh_token(data: dict, db: AsyncSession):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    user_id = data.get("sub")
    if user_id:
        refresh_token_record = db_models.RefreshToken(
            refresh_token=encoded_jwt,
            user_id=int(user_id),
            expires_at=expire,
            revoked=False
        )
        db.add(refresh_token_record)
        await db.flush()
        logger.info(f"Refresh token created and stored for user {user_id}, expires at {expire}")
        await log_user_action(
            db=db,
            user_id=int(user_id),
            action="REFRESH_TOKEN_CREATED",
            resource_type="REFRESH_TOKEN",
            resource_id=encoded_jwt[:16],
            extra_data={"expires_at": expire.isoformat()}
        )
    return encoded_jwt


def verify_access_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.warning("Access token verification failed: missing user_id in payload")
            log_security_event("INVALID_TOKEN", {"reason": "missing_user_id"})
            raise credentials_exception
        logger.debug(f"Access token verified successfully for user {user_id}")
        token_data = tk.TokenData(id=user_id)
        return token_data
    except JWTError as e:
        logger.warning(f"JWT Error during access token verification: {e}")
        log_security_event("JWT_VERIFICATION_FAILED", {"error": str(e)})
        raise credentials_exception
    except Exception as e:
        logger.error(f"Unexpected error in verify_access_token: {e}")
        log_security_event("TOKEN_VERIFICATION_ERROR", {"error": str(e)}, severity="ERROR")
        raise credentials_exception


def verify_refresh_token(token: str, credentials_exception):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            logger.warning("Refresh token verification failed: missing user_id in payload")
            log_security_event("INVALID_REFRESH_TOKEN", {"reason": "missing_user_id"})
            raise credentials_exception
        logger.debug(f"Refresh token verified successfully for user {user_id}")
        token_data = tk.TokenData(id=user_id)
        return token_data
    except JWTError as e:
        logger.warning(f"JWT Error during refresh token verification: {e}")
        log_security_event("REFRESH_TOKEN_VERIFICATION_FAILED", {"error": str(e)})
        raise credentials_exception
    except Exception as e:
        logger.error(f"Unexpected error in verify_refresh_token: {e}")
        log_security_event("REFRESH_TOKEN_ERROR", {"error": str(e)}, severity="ERROR")
        raise credentials_exception


async def verify_refresh_token_with_db(token: str, db: AsyncSession, credentials_exception):
    token_data = verify_refresh_token(token, credentials_exception)
    
    result = await db.execute(
        select(db_models.RefreshToken).where(db_models.RefreshToken.refresh_token == token)
    )
    db_token = result.scalar_one_or_none()
    
    if not db_token:
        logger.warning(f"Refresh token not found in database")
        log_security_event("REFRESH_TOKEN_NOT_IN_DB", {"token_prefix": token[:20]})
        raise credentials_exception
    
    if db_token.revoked:
        logger.warning(f"Attempted use of revoked refresh token for user {token_data.id}")
        log_security_event("REVOKED_TOKEN_USED", {"user_id": token_data.id}, severity="WARNING")
        raise credentials_exception
    
    from datetime import datetime, timezone
    if db_token.expires_at < datetime.now(timezone.utc):
        logger.warning(f"Refresh token expired for user {token_data.id}")
        log_security_event("EXPIRED_REFRESH_TOKEN", {"user_id": token_data.id})
        raise credentials_exception
    
    return token_data


def get_token_from_header_or_cookie(
        request: Request,
        token_from_header: str = Depends(oauth2_scheme_optional)
) -> str | None:
    token_from_cookie = request.cookies.get("access_token")
    if token_from_cookie:
        try:
            return token_from_cookie.split(" ")[1]
        except IndexError:
            return None

    if token_from_header and token_from_header != "cookie_auth_user":
        return token_from_header

    return None


async def get_current_user(
        token: str = Depends(get_token_from_header_or_cookie),
        db: AsyncSession = Depends(get_db)
) -> db_models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if token is None:
        logger.warning("No token provided in Authorization header or access_token cookie")
        raise credentials_exception

    token_data = verify_access_token(token, credentials_exception)

    if token_data.id is None:
        raise credentials_exception

    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(db_models.User)
        .options(selectinload(db_models.User.merchant_info), selectinload(db_models.User.verified_info))
        .where(db_models.User.id == int(token_data.id))
    )
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user


async def get_user_from_api_key(api_key: str, db: AsyncSession) -> db_models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "ApiKey"},
    )
    if not api_key:
        logger.warning("No API key provided")
        log_security_event("NO_API_KEY_PROVIDED", {"endpoint": "protected_resource"})
        raise credentials_exception
    logger.debug(f"API key received: {api_key[:15]}...")

    result = await db.execute(select(db_models.APIKey).where(db_models.APIKey.is_active == True))
    api_keys = result.scalars().all()

    matched_key = None
    for key in api_keys:
        if verify_password(api_key, key.api_key):
            matched_key = key
            break
    if not matched_key:
        logger.warning(f"Invalid API key attempted: {api_key[:15]}...")
        log_security_event("INVALID_API_KEY", {"key_prefix": api_key[:15]}, severity="WARNING")
        raise credentials_exception

    matched_key.last_used_at = datetime.now(timezone.utc)
    await db.commit()

    merchant_result = await db.execute(select(db_models.MerchantAccount).where(db_models.MerchantAccount.merchant_id == matched_key.merchant_id))
    merchant = merchant_result.scalar_one_or_none()
    if not merchant:
        logger.error(f"Merchant not found for API key {matched_key.id}")
        log_security_event("MERCHANT_NOT_FOUND_FOR_API_KEY", {"key_id": matched_key.id}, severity="ERROR")
        raise credentials_exception

    from sqlalchemy.orm import selectinload
    user_result = await db.execute(
        select(db_models.User)
        .options(selectinload(db_models.User.merchant_info), selectinload(db_models.User.verified_info))
        .where(db_models.User.id == merchant.user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        logger.error(f"User not found for merchant {merchant.merchant_id}")
        log_security_event("USER_NOT_FOUND_FOR_MERCHANT", {"merchant_id": merchant.merchant_id}, severity="ERROR")
        raise credentials_exception

    logger.info(f"User {user.id} authenticated via API key {matched_key.id}")
    return user


async def get_current_user_or_api_key(
        request: Request,
        token: str = Depends(oauth2_scheme_optional),
        api_key: str = Depends(api_key_header),
        db: AsyncSession = Depends(get_db)
):
    logger.debug(f"Auth attempt - API Key present: {api_key is not None}, Token present: {token is not None}")
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if api_key:
        logger.info("Attempting API key authentication")
        try:
            user = await get_user_from_api_key(api_key, db)
            logger.info(f"Successfully authenticated user {user.id} via API key")
            return user
        except HTTPException as e:
            logger.warning(f"API key authentication failed: {e.detail}")

    cookie_token_str = request.cookies.get("access_token")
    if cookie_token_str:
        logger.info("Attempting JWT cookie authentication")
        try:
            cookie_token = cookie_token_str.split(" ")[1]
            user = await get_current_user(cookie_token, db)
            logger.info(f"Successfully authenticated user {user.id} via JWT cookie")
            return user
        except (IndexError, HTTPException):
            logger.warning("JWT cookie authentication failed")

    if token and token != "cookie_auth_user":
        logger.info("Attempting JWT header authentication")
        try:
            user = await get_current_user(token, db)
            logger.info(f"Successfully authenticated user {user.id} via JWT header")
            return user
        except HTTPException:
            logger.warning("JWT header authentication failed")

    logger.warning("No valid authentication provided - no API key, cookie, or valid header token found")
    log_security_event("NO_AUTH_PROVIDED", {"endpoint": "protected_resource"})
    raise credentials_exception


async def get_current_superadmin(
        current_user: db_models.User = Depends(get_current_user)
) -> db_models.User:
    if not current_user.is_superadmin:
        logger.warning(f"Non-admin user {current_user.id} ({current_user.email}) attempted superadmin only action.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operation not permitted: Requires superadmin privileges"
        )
    logger.info(f"Superadmin action permitted for user {current_user.id}")
    return current_user