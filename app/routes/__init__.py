from fastapi import APIRouter

from app.routes.imgkit import router as ImgKitRouter
from app.routes.conversation import router as ConversationRouter
from app.routes.pooling import router as PoolingRouter
from app.routes.app import router as AppRouter
from app.routes.model import router as ModelRouter
from app.routes.profile import router as ProfileRouter
from app.routes.gallery import router as GalleryRouter

router = APIRouter(prefix="/api", tags=["Protected Routes"])

router.include_router(ImgKitRouter)
router.include_router(ConversationRouter)
router.include_router(PoolingRouter)
router.include_router(AppRouter)
router.include_router(ModelRouter)
router.include_router(ProfileRouter)
router.include_router(GalleryRouter)
