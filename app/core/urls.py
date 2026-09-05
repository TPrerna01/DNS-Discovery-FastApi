from fastapi import APIRouter
from app.users.urls import auth_router
from app.domains.urls import domain_router
from app.scans.urls import scan_router
from app.assets.urls import asset_router

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth_router)
api_router.include_router(domain_router)
api_router.include_router(scan_router)
api_router.include_router(asset_router)
