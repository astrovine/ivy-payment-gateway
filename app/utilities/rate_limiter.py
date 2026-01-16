import time
from collections import defaultdict
from functools import wraps
from typing import Callable, Optional
from fastapi import HTTPException, Request, status
from .logger import setup_logger, log_security_event

logger = setup_logger(__name__)


class RateLimiter:
    def __init__(self):
        self.requests: dict[str, list[float]] = defaultdict(list)
        self.blocked_until: dict[str, float] = {}
    
    def _cleanup_old_requests(self, key: str, window_seconds: int):
        current_time = time.time()
        cutoff = current_time - window_seconds
        self.requests[key] = [t for t in self.requests[key] if t > cutoff]
    
    def is_rate_limited(
        self, 
        key: str, 
        max_requests: int, 
        window_seconds: int,
        block_duration_seconds: int = 300
    ) -> tuple[bool, Optional[int]]:
        current_time = time.time()
        
        if key in self.blocked_until:
            if current_time < self.blocked_until[key]:
                remaining = int(self.blocked_until[key] - current_time)
                return True, remaining
            else:
                del self.blocked_until[key]
        
        self._cleanup_old_requests(key, window_seconds)
        
        if len(self.requests[key]) >= max_requests:
            self.blocked_until[key] = current_time + block_duration_seconds
            log_security_event(
                "RATE_LIMIT_EXCEEDED",
                {"key": key, "requests": len(self.requests[key]), "limit": max_requests},
                severity="WARNING"
            )
            return True, block_duration_seconds
        
        self.requests[key].append(current_time)
        return False, None
    
    def reset(self, key: str):
        if key in self.requests:
            del self.requests[key]
        if key in self.blocked_until:
            del self.blocked_until[key]


rate_limiter = RateLimiter()


def rate_limit(
    max_requests: int = 5,
    window_seconds: int = 60,
    block_duration_seconds: int = 300,
    key_func: Optional[Callable[[Request], str]] = None
):
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request: Request = kwargs.get("request")
            if not request:
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if request:
                if key_func:
                    limit_key = key_func(request)
                else:
                    client_ip = request.client.host if request.client else "unknown"
                    limit_key = f"{client_ip}:{request.url.path}"
                
                is_limited, retry_after = rate_limiter.is_rate_limited(
                    limit_key, max_requests, window_seconds, block_duration_seconds
                )
                
                if is_limited:
                    logger.warning(f"Rate limit exceeded for {limit_key}")
                    raise HTTPException(
                        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                        detail=f"Too many requests. Try again in {retry_after} seconds.",
                        headers={"Retry-After": str(retry_after)}
                    )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def login_rate_limit_key(request: Request) -> str:
    client_ip = request.client.host if request.client else "unknown"
    return f"login:{client_ip}"


def forgot_password_rate_limit_key(request: Request) -> str:
    client_ip = request.client.host if request.client else "unknown"
    return f"forgot_password:{client_ip}"


def register_rate_limit_key(request: Request) -> str:
    client_ip = request.client.host if request.client else "unknown"
    return f"register:{client_ip}"
