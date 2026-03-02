from fastapi import APIRouter

from .users import router as user_router
from .files import router as file_router


router = APIRouter()

router.include_router(user_router)
router.include_router(file_router)
