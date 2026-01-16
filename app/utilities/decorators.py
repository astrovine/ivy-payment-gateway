from functools import wraps
from typing import Callable, Optional
from fastapi import HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from ..models import db_models
from .logger import log_user_action, setup_logger

logger = setup_logger(__name__)


def log_action(
    action: str,
    resource_type: str,
    get_resource_id: Optional[Callable] = None
):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Optional[Request] = kwargs.get("request")
            db: Optional[AsyncSession] = kwargs.get("db")
            current_user: Optional[db_models.User] = kwargs.get("current_user")
            
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            result = await func(*args, **kwargs)
            
            if db and current_user:
                ip_address = request.client.host if request and request.client else "unknown"
                user_agent = request.headers.get("user-agent") if request else None
                
                resource_id = None
                if get_resource_id:
                    try:
                        resource_id = get_resource_id(kwargs, result)
                    except Exception:
                        pass
                
                merchant_id = None
                if hasattr(current_user, 'merchant_info') and current_user.merchant_info:
                    merchant_id = current_user.merchant_info.merchant_id
                
                await log_user_action(
                    db=db,
                    user_id=current_user.id,
                    action=action,
                    resource_type=resource_type,
                    resource_id=resource_id,
                    merchant_id=merchant_id,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
            
            return result
        return wrapper
    return decorator


def require_merchant(func: Callable):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        current_user: Optional[db_models.User] = kwargs.get("current_user")
        
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        if not hasattr(current_user, 'merchant_info') or not current_user.merchant_info:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Merchant account required. Please create a merchant account first."
            )
        
        return await func(*args, **kwargs)
    return wrapper


def require_kyc_verified(func: Callable):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        current_user: Optional[db_models.User] = kwargs.get("current_user")
        
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        if not hasattr(current_user, 'merchant_info') or not current_user.merchant_info:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Merchant account required"
            )
        
        merchant = current_user.merchant_info
        if merchant.kyc_status != db_models.KYCStatus.verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="KYC verification required to perform this action"
            )
        
        return await func(*args, **kwargs)
    return wrapper


def require_admin(func: Callable):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        current_user: Optional[db_models.User] = kwargs.get("current_user")
        
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        if not current_user.is_superadmin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        
        return await func(*args, **kwargs)
    return wrapper


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"
