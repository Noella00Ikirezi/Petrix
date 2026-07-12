"""API v1 main router."""
from fastapi import APIRouter

from app.api.v1 import auth, users, assets, vulnerabilities, dashboard, system, audit_logs, hardening, agent_download, feed

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(assets.router, prefix="/assets", tags=["Assets"])
api_router.include_router(vulnerabilities.router, prefix="/vulnerabilities", tags=["Vulnerabilities"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])
api_router.include_router(system.router, prefix="/system", tags=["System"])
api_router.include_router(audit_logs.router, prefix="/audit-logs", tags=["Audit Logs"])
api_router.include_router(hardening.router, prefix="/hardening", tags=["Hardening"])
api_router.include_router(agent_download.router, prefix="/agent", tags=["Agent"])
api_router.include_router(feed.router, prefix="/feed", tags=["Security Feed"])
