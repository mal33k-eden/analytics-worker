from fastapi import APIRouter

from app.routes import track

api_router = APIRouter()
api_router.include_router(track.router)
