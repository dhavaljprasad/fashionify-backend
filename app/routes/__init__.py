from fastapi import APIRouter

from app.routes.imgkit import router as ImgKitRouter

router = APIRouter(prefix="/api", tags=["Protected Routes"])

router.include_router(ImgKitRouter)
