from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.routers import authentication, account, charges, merchant, api_keys, kyc, verification, admin_router, payout_account, payouts, webhooks
from app.routers import settlements
from app.models.base import Base
from app.utilities.config import settings
from app.utilities.db_con import engine, async_engine
from app.middleware.logging_middleware import RequestLoggingMiddleware, SecurityLoggingMiddleware
from app.utilities.logger import app_logger
from app.celery_worker import celery_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    app_logger.info("Payment Gateway starting up...")
    Base.metadata.create_all(bind=engine)
    yield
    await async_engine.dispose()
    app_logger.info("Payment Gateway shutting down...")


app = FastAPI(title="Payment Gateway API", version="1.0.0", lifespan=lifespan)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityLoggingMiddleware)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET_KEY,
    same_site="lax",
    https_only=False,
    max_age=60 * 15
)
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost",
    "http://localhost:3000",
    "http://51.21.130.249:5173",
    "http://ivypayments.ddns.net:5173"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(authentication.router)
app.include_router(account.router)
app.include_router(charges.router)
app.include_router(merchant.router)
app.include_router(api_keys.router)
app.include_router(kyc.router)
app.include_router(verification.router)
app.include_router(admin_router.router)
app.include_router(payout_account.router)
app.include_router(payouts.router)
app.include_router(webhooks.router)
app.include_router(settlements.router)
from app.routers.notifications import router as notifications_router
app.include_router(notifications_router)
from app.routers.two_factor import router as two_factor_router
app.include_router(two_factor_router)

celery_app.autodiscover_tasks(['app'])
