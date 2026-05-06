from fastapi import APIRouter

from app.routes.imgkit import router as ImgKitRouter
from app.routes.conversation import router as ConversationRouter

router = APIRouter(prefix="/api", tags=["Protected Routes"])

router.include_router(ImgKitRouter)
router.include_router(ConversationRouter)
