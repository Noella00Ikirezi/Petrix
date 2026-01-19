"""System endpoints - License, updates, health checks."""
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
import httpx

from app.config import settings
from app.core.licensing import (
    LicenseInfo,
    LicenseManager,
    LicenseTier,
    get_current_license,
    set_license,
    TIER_FEATURES,
)
from app.core.permissions import Permission
from app.api.v1.deps import require_permission
from app.infrastructure.database.models import User

router = APIRouter()

# Current version
APP_VERSION = "1.0.0"
UPDATE_CHECK_URL = "https://api.grc-platform.io/v1/updates"  # Your update server


class VersionInfo(BaseModel):
    """Application version information."""
    version: str
    build_date: str
    python_version: str


class UpdateInfo(BaseModel):
    """Update availability information."""
    current_version: str
    latest_version: str
    update_available: bool
    release_notes: Optional[str] = None
    download_url: Optional[str] = None
    is_security_update: bool = False


class LicenseActivateRequest(BaseModel):
    """License activation request."""
    license_key: str


class LicenseResponse(BaseModel):
    """License information response."""
    license_id: str
    organization: str
    tier: str
    issued_at: datetime
    expires_at: datetime
    is_valid: bool
    days_remaining: int
    features: dict


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    database: str
    redis: str
    license_tier: str
    license_valid: bool


class SystemStatsResponse(BaseModel):
    """System statistics response."""
    total_assets: int
    total_users: int
    scans_this_month: int
    license_limits: dict
    within_limits: bool


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint for monitoring.
    No authentication required.
    """
    from app.infrastructure.database import SessionLocal
    import redis

    # Check database
    db_status = "healthy"
    try:
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
    except Exception:
        db_status = "unhealthy"

    # Check Redis
    redis_status = "healthy"
    try:
        r = redis.from_url(settings.redis_url)
        r.ping()
    except Exception:
        redis_status = "unhealthy"

    # Get license info
    license_info = get_current_license()

    overall_status = "healthy" if db_status == "healthy" and redis_status == "healthy" else "degraded"

    return HealthResponse(
        status=overall_status,
        version=APP_VERSION,
        database=db_status,
        redis=redis_status,
        license_tier=license_info.tier.value,
        license_valid=license_info.is_valid,
    )


@router.get("/version", response_model=VersionInfo)
async def get_version():
    """Get current application version."""
    import sys
    return VersionInfo(
        version=APP_VERSION,
        build_date="2024-01-15",
        python_version=sys.version.split()[0],
    )


@router.get("/updates", response_model=UpdateInfo)
async def check_updates(
    current_user: User = Depends(require_permission(Permission.SYSTEM_SETTINGS)),
):
    """
    Check for available updates.
    Contacts the update server to check for new versions.
    """
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                UPDATE_CHECK_URL,
                params={
                    "current_version": APP_VERSION,
                    "tier": get_current_license().tier.value,
                }
            )

            if response.status_code == 200:
                data = response.json()
                return UpdateInfo(
                    current_version=APP_VERSION,
                    latest_version=data.get("latest_version", APP_VERSION),
                    update_available=data.get("update_available", False),
                    release_notes=data.get("release_notes"),
                    download_url=data.get("download_url"),
                    is_security_update=data.get("is_security_update", False),
                )
    except Exception:
        pass  # Fail silently if update server unreachable

    # Return current version info if update check fails
    return UpdateInfo(
        current_version=APP_VERSION,
        latest_version=APP_VERSION,
        update_available=False,
    )


@router.get("/license", response_model=LicenseResponse)
async def get_license(
    current_user: User = Depends(require_permission(Permission.SYSTEM_SETTINGS)),
):
    """Get current license information."""
    license_info = get_current_license()

    return LicenseResponse(
        license_id=license_info.license_id,
        organization=license_info.organization,
        tier=license_info.tier.value,
        issued_at=license_info.issued_at,
        expires_at=license_info.expires_at,
        is_valid=license_info.is_valid,
        days_remaining=license_info.days_remaining,
        features=license_info.features.model_dump(),
    )


@router.post("/license/activate", response_model=LicenseResponse)
async def activate_license(
    request: LicenseActivateRequest,
    current_user: User = Depends(require_permission(Permission.SYSTEM_SETTINGS)),
):
    """
    Activate a new license key.
    Validates the license and applies it if valid.
    """
    license_info = set_license(request.license_key)

    if license_info is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid license key. Please check the key and try again.",
        )

    if not license_info.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="License has expired. Please contact support for renewal.",
        )

    # TODO: Persist license key to database or file for restart persistence

    return LicenseResponse(
        license_id=license_info.license_id,
        organization=license_info.organization,
        tier=license_info.tier.value,
        issued_at=license_info.issued_at,
        expires_at=license_info.expires_at,
        is_valid=license_info.is_valid,
        days_remaining=license_info.days_remaining,
        features=license_info.features.model_dump(),
    )


@router.get("/license/tiers")
async def get_license_tiers():
    """Get available license tiers and their features (public info)."""
    tiers = {}
    for tier in LicenseTier:
        features = TIER_FEATURES[tier]
        tiers[tier.value] = {
            "name": tier.value.title(),
            "features": features.model_dump(),
        }
    return tiers


@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    current_user: User = Depends(require_permission(Permission.SYSTEM_SETTINGS)),
):
    """Get system statistics and license limit usage."""
    from sqlalchemy import func
    from app.infrastructure.database import SessionLocal
    from app.infrastructure.database.models import Asset, User as UserModel, Scan

    db = SessionLocal()
    try:
        # Count current usage
        total_assets = db.query(Asset).count()
        total_users = db.query(UserModel).filter(UserModel.is_active == True).count()

        # Count scans this month
        from datetime import datetime
        first_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        scans_this_month = db.query(Scan).filter(Scan.created_at >= first_of_month).count()

        # Get license limits
        license_info = get_current_license()
        limits = {
            "max_assets": license_info.features.max_assets,
            "max_users": license_info.features.max_users,
            "max_scans_per_month": license_info.features.max_scans_per_month,
        }

        # Check if within limits
        within_limits = True
        if limits["max_assets"] != -1 and total_assets >= limits["max_assets"]:
            within_limits = False
        if limits["max_users"] != -1 and total_users >= limits["max_users"]:
            within_limits = False
        if limits["max_scans_per_month"] != -1 and scans_this_month >= limits["max_scans_per_month"]:
            within_limits = False

        return SystemStatsResponse(
            total_assets=total_assets,
            total_users=total_users,
            scans_this_month=scans_this_month,
            license_limits=limits,
            within_limits=within_limits,
        )
    finally:
        db.close()


# Admin endpoint to generate licenses (would be on separate server in production)
@router.post("/license/generate")
async def generate_license(
    organization: str,
    tier: LicenseTier = LicenseTier.PROFESSIONAL,
    valid_days: int = 365,
    current_user: User = Depends(require_permission(Permission.SYSTEM_SETTINGS)),
):
    """
    Generate a new license key (admin only).

    In production, this endpoint would be on a separate license server,
    not on the client installation. Included here for demo purposes.
    """
    license_key = LicenseManager.generate_license(
        organization=organization,
        tier=tier,
        valid_days=valid_days,
    )

    return {
        "license_key": license_key,
        "organization": organization,
        "tier": tier.value,
        "valid_days": valid_days,
    }
