from fastapi import APIRouter

from .users import router as user_router
from .files import router as file_router
from .directories import router as directory_router


router = APIRouter()

router.include_router(user_router)
router.include_router(file_router)
router.include_router(directory_router)
