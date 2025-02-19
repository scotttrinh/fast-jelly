from __future__ import annotations

import logging
import sys

from fastapi import FastAPI, APIRouter

from app import auth, users, events, ui


formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
stream_handler = logging.StreamHandler(sys.stdout)
stream_handler.setFormatter(formatter)

logger = logging.getLogger("fast_jelly")
logger.setLevel(logging.DEBUG)
logger.addHandler(stream_handler)

auth_core_logger = logging.getLogger("gel_auth_core")
auth_core_logger.setLevel(logging.DEBUG)
auth_core_logger.addHandler(stream_handler)

fast_api = FastAPI()
fast_api.include_router(ui.router)
fast_api.include_router(auth.router)

api_router = APIRouter()
api_router.include_router(users.router)
api_router.include_router(events.router)

fast_api.include_router(api_router, prefix="/api")
