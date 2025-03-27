from fastapi import APIRouter
from apis import refrigerator, air_conditioner, robot_cleaner, routine
from logging_config import setup_logger

# API 라우터용 로거 설정
logger = setup_logger("api_router")

router = APIRouter()

logger.info("Initializing API routers")
router.include_router(refrigerator.router)
logger.info("Refrigerator router initialized")
router.include_router(air_conditioner.router)
logger.info("Air conditioner router initialized")
router.include_router(robot_cleaner.router)
logger.info("Robot cleaner router initialized")
router.include_router(routine.router)
logger.info("Routine router initialized")
