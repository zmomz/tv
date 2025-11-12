import logging
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api import auth, keys, webhooks, position_groups, logs, config, dashboard, positions
from app.db.session import engine
from app.db.base import Base
from app.core.config import settings
from app.middleware.auth_middleware import AuthMiddleware

# Setup logging
logging.basicConfig(level=settings.APP_LOG_LEVEL.upper())
logger = logging.getLogger(__name__)

# Create all tables in the database
Base.metadata.create_all(bind=engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Application startup...")
    from app.tasks.log_cleanup import scheduler
    if not scheduler.running:
        scheduler.start()
    yield
    # Shutdown
    logger.info("Application shutdown...")
    if scheduler.running:
        scheduler.shutdown()

app = FastAPI(lifespan=lifespan)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(AuthMiddleware)

# Routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(keys.router, prefix="/api/keys", tags=["keys"])
app.include_router(webhooks.router, prefix="/api/webhook", tags=["webhook"])
app.include_router(position_groups.router, prefix="/api/position-groups", tags=["position-groups"])
app.include_router(logs.router, prefix="/api/logs", tags=["logs"])
app.include_router(config.router, prefix="/api/config", tags=["config"])
app.include_router(dashboard.router, prefix="/api/dashboard", tags=["dashboard"])
app.include_router(positions.router, prefix="/api/positions", tags=["positions"])

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors(), "body": exc.body},
    )

@app.get("/")
def read_root():
    return {"message": "Trading Engine is running"}
