from fastapi import FastAPI
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1.router import router as v1_router
from app.core.config import settings

is_production = settings.environment.lower() == "production"

app = FastAPI(
    title="Research Paper Manager API",
    version="0.1.0",
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.trusted_hosts,
)

app.include_router(v1_router, prefix="/api/v1", tags=["v1"])
