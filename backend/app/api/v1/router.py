"""API v1 main router."""
from fastapi import APIRouter

from app.api.v1 import auth, users, assets, vulnerabilities, scans, dashboard, system, smsi, clients

api_router = APIRouter()

# Include all routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(assets.router, prefix="/assets", tags=["Assets"])
api_router.include_router(
    vulnerabilities.router, prefix="/vulnerabilities", tags=["Vulnerabilities"]
)
api_router.include_router(scans.router, prefix="/scans", tags=["Scans"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(system.router, prefix="/system", tags=["System"])
api_router.include_router(smsi.router)
api_router.include_router(clients.router)
