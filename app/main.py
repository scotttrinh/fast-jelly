from __future__ import annotations

from fastapi import FastAPI, APIRouter

from app import auth, users, events, ui


fast_api = FastAPI()
fast_api.include_router(ui.router)

api_router = APIRouter()
api_router.include_router(users.router)
api_router.include_router(events.router)
api_router.include_router(auth.router)

fast_api.include_router(api_router, prefix="/api")
