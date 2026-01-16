import time
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from typing import Callable

from ..utilities.logger import log_api_request, log_security_event, api_logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        method = request.method
        path = request.url.path
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        user_id = getattr(request.state, "user_id", None)

        api_logger.info(
            f"Incoming {method} {path} from {client_ip}",
            extra={
                "method": method,
                "endpoint": path,
                "ip_address": client_ip,
                "user_agent": user_agent,
                "user_id": user_id
            }
        )

        response: Response | None = None
        status_code: int = 500

        try:
            response = await call_next(request)
            status_code = response.status_code

        except HTTPException as e:
            status_code = e.status_code
            api_logger.warning(
                f"HTTP Exception: {method} {path} - {status_code}: {e.detail}",
                extra={
                    "method": method,
                    "endpoint": path,
                    "status_code": status_code,
                    "ip_address": client_ip,
                    "user_id": user_id,
                    "error": e.detail
                }
            )
            raise

        except Exception as e:
            status_code = 500

            api_logger.error(
                f"Unexpected Error: {method} {path} - {str(e)}",
                extra={
                    "method": method,
                    "endpoint": path,
                    "status_code": status_code,
                    "ip_address": client_ip,
                    "user_id": user_id,
                    "error": str(e)
                },
                exc_info=True
            )
            raise

        finally:
            # Calculate response time
            process_time = (time.time() - start_time) * 1000
            log_api_request(
                method=method,
                endpoint=path,
                status_code=status_code,
                response_time=process_time,
                user_id=user_id,
                ip_address=client_ip
            )

            if process_time > 1000:
                api_logger.warning(
                    f"Slow request detected: {method} {path} took {process_time:.2f}ms",
                    extra={
                        "method": method,
                        "endpoint": path,
                        "response_time": process_time,
                        "ip_address": client_ip
                    }
                )

            if response is not None:
                response.headers["X-Process-Time"] = str(process_time)

        return response  # type: ignore[return-value]


class SecurityLoggingMiddleware(BaseHTTPMiddleware):
    SUSPICIOUS_PATTERNS = [
        "SELECT", "DROP", "INSERT", "UPDATE", "DELETE",  # SQL injection attempts
        "<script>", "javascript:", "onerror=",  # XSS attempts
        "../", "..\\",  # Path traversal
        "<?php", "<?=",  # Code injection
        "UNION", "OR 1=1", "' OR '", "-- ", ";--",  # Additional SQL patterns
    ]
    
    BLOCKED_PATTERNS = [
        "' OR '", "OR 1=1", "UNION SELECT", "DROP TABLE", "DELETE FROM",
        "<script>", "javascript:", "onerror=", "<?php",
    ]
    
    SAFE_PATHS = [
        "/docs", "/openapi.json", "/redoc",
    ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        full_path = str(request.url)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        is_safe_path = any(request.url.path.startswith(safe) for safe in self.SAFE_PATHS)
        
        if not is_safe_path:
            for pattern in self.BLOCKED_PATTERNS:
                if pattern.lower() in full_path.lower():
                    log_security_event(
                        "BLOCKED_MALICIOUS_REQUEST",
                        {
                            "pattern": pattern,
                            "path": request.url.path,
                            "ip_address": client_ip,
                            "user_agent": user_agent,
                            "full_url": full_path[:200]
                        },
                        severity="CRITICAL"
                    )
                    from starlette.responses import JSONResponse
                    return JSONResponse(
                        status_code=400,
                        content={"detail": "Bad request"}
                    )
            
            for pattern in self.SUSPICIOUS_PATTERNS:
                if pattern.lower() in full_path.lower():
                    log_security_event(
                        "SUSPICIOUS_REQUEST",
                        {
                            "pattern": pattern,
                            "path": request.url.path,
                            "ip_address": client_ip,
                            "user_agent": user_agent
                        },
                        severity="WARNING"
                    )
                    break

        response = await call_next(request)
        return response

