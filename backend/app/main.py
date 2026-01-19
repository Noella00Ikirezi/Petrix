"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.config import settings
from app.infrastructure.database import Base, engine
from app.api.v1.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    # Startup
    logger.info("Starting GRC Platform API...")

    # Create tables
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created")

    # Create default admin user if not exists
    from app.infrastructure.database import SessionLocal
    from app.infrastructure.database.models import User
    from app.core.security import get_password_hash
    from app.core.permissions import UserRole

    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.email == settings.admin_email).first()
        if not admin:
            admin = User(
                email=settings.admin_email,
                password_hash=get_password_hash(settings.admin_password),
                first_name="Admin",
                last_name="User",
                role=UserRole.ADMIN,
                is_active=True,
            )
            db.add(admin)
            db.commit()
            logger.info(f"Admin user created: {settings.admin_email}")
    finally:
        db.close()

    yield

    # Shutdown
    logger.info("Shutting down GRC Platform API...")


app = FastAPI(
    title=settings.app_name,
    description="GRC Platform API - Governance, Risk, and Compliance Management",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API router
app.include_router(api_router, prefix=settings.api_v1_prefix)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}
