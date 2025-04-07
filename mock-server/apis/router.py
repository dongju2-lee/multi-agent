from fastapi import APIRouter
from apis import refrigerator, microwave, induction, food_manager, routine
from logging_config import setup_logger

# API 라우터용 로거 설정
logger = setup_logger("api_router")

# 메인 라우터
router = APIRouter()

logger.info("Initializing API routers")
router.include_router(refrigerator.router)
logger.info("Refrigerator router initialized")
router.include_router(microwave.router)
logger.info("Microwave router initialized")
router.include_router(induction.router)
logger.info("Induction router initialized")
router.include_router(food_manager.router)
logger.info("Food manager router initialized")
router.include_router(routine.router)
logger.info("Routine router initialized")
