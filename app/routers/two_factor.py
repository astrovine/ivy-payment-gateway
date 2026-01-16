from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import db_models
from ..utilities import Oauth2 as au
from ..utilities.db_con import get_db
from ..utilities.two_factor import generate_totp_secret, generate_qr_code_base64, verify_totp, get_totp_uri
from ..utilities.logger import log_user_action, setup_logger
from ..services.email_service import email_service

router = APIRouter(prefix="/api/v1/2fa", tags=["Two-Factor Authentication"])
logger = setup_logger(__name__)


class Enable2FAResponse(BaseModel):
    qr_code_base64: str
    manual_entry_key: str
    message: str


class Verify2FARequest(BaseModel):
    code: str


class Verify2FAResponse(BaseModel):
    success: bool
    message: str


@router.post("/enable", response_model=Enable2FAResponse)
async def enable_2fa(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user)
):
    ip_address = request.client.host if request.client else "unknown"
    logger.info(f"User {current_user.id} attempting to enable 2FA from {ip_address}")
    
    if not current_user.merchant_info:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Merchant account required")
    
    result = await db.execute(
        select(db_models.MerchantSettings).where(
            db_models.MerchantSettings.merchant_id == current_user.merchant_info.merchant_id
        )
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        settings = db_models.MerchantSettings(merchant_id=current_user.merchant_info.merchant_id)
        db.add(settings)
        await db.flush()
    
    if settings.two_factor_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA is already enabled")
    
    encrypted_secret = generate_totp_secret()
    settings.two_factor_secret = encrypted_secret
    
    await db.flush()
    
    qr_code = generate_qr_code_base64(current_user.email, encrypted_secret)
    totp_uri = get_totp_uri(current_user.email, encrypted_secret)
    
    from ..utilities.encryption import decrypt_value
    manual_key = decrypt_value(encrypted_secret)
    
    await log_user_action(
        db=db,
        user_id=current_user.id,
        action="2FA_SETUP_INITIATED",
        resource_type="USER",
        merchant_id=current_user.merchant_info.merchant_id,
        ip_address=ip_address,
        user_agent=request.headers.get("user-agent")
    )
    await db.commit()
    
    logger.info(f"2FA setup initiated for user {current_user.id}")
    
    return Enable2FAResponse(
        qr_code_base64=qr_code,
        manual_entry_key=manual_key,
        message="Scan the QR code with your authenticator app, then verify with a code"
    )


@router.post("/verify", response_model=Verify2FAResponse)
async def verify_and_enable_2fa(
    data: Verify2FARequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user)
):
    ip_address = request.client.host if request.client else "unknown"
    logger.info(f"User {current_user.id} verifying 2FA code from {ip_address}")
    
    if not current_user.merchant_info:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Merchant account required")
    
    result = await db.execute(
        select(db_models.MerchantSettings).where(
            db_models.MerchantSettings.merchant_id == current_user.merchant_info.merchant_id
        )
    )
    settings = result.scalar_one_or_none()
    
    if not settings or not settings.two_factor_secret:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA setup not initiated")
    
    if not verify_totp(settings.two_factor_secret, data.code):
        logger.warning(f"Invalid 2FA code for user {current_user.id}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code")
    
    settings.two_factor_enabled = True
    
    await log_user_action(
        db=db,
        user_id=current_user.id,
        action="2FA_ENABLED",
        resource_type="USER",
        merchant_id=current_user.merchant_info.merchant_id,
        ip_address=ip_address,
        user_agent=request.headers.get("user-agent")
    )
    await db.commit()
    
    email_service.send_2fa_enabled_notification(current_user.email)
    
    logger.info(f"2FA enabled for user {current_user.id}")
    
    return Verify2FAResponse(success=True, message="Two-factor authentication enabled successfully")


@router.post("/disable", response_model=Verify2FAResponse)
async def disable_2fa(
    data: Verify2FARequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user)
):
    ip_address = request.client.host if request.client else "unknown"
    logger.info(f"User {current_user.id} attempting to disable 2FA from {ip_address}")
    
    if not current_user.merchant_info:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Merchant account required")
    
    result = await db.execute(
        select(db_models.MerchantSettings).where(
            db_models.MerchantSettings.merchant_id == current_user.merchant_info.merchant_id
        )
    )
    settings = result.scalar_one_or_none()
    
    if not settings or not settings.two_factor_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="2FA is not enabled")
    
    if not verify_totp(settings.two_factor_secret, data.code):
        logger.warning(f"Invalid 2FA code for disable by user {current_user.id}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code")
    
    settings.two_factor_enabled = False
    settings.two_factor_secret = None
    
    await log_user_action(
        db=db,
        user_id=current_user.id,
        action="2FA_DISABLED",
        resource_type="USER",
        merchant_id=current_user.merchant_info.merchant_id,
        ip_address=ip_address,
        user_agent=request.headers.get("user-agent")
    )
    await db.commit()
    
    logger.info(f"2FA disabled for user {current_user.id}")
    
    return Verify2FAResponse(success=True, message="Two-factor authentication disabled")


@router.get("/status")
async def get_2fa_status(
    db: AsyncSession = Depends(get_db),
    current_user: db_models.User = Depends(au.get_current_user)
):
    if not current_user.merchant_info:
        return {"enabled": False, "available": False, "message": "Merchant account required"}
    
    result = await db.execute(
        select(db_models.MerchantSettings).where(
            db_models.MerchantSettings.merchant_id == current_user.merchant_info.merchant_id
        )
    )
    settings = result.scalar_one_or_none()
    
    if not settings:
        return {"enabled": False, "available": True}
    
    return {"enabled": settings.two_factor_enabled, "available": True}
