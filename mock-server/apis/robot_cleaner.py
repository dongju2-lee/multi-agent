from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.robot_cleaner_service import RobotCleanerService
from logging_config import setup_logger

# 로봇청소기 API용 로거 설정
logger = setup_logger("robot_cleaner_api")

router = APIRouter(prefix="/robot-cleaner", tags=["robot-cleaner"])
service = RobotCleanerService()

class StateRequest(BaseModel):
    state: str

class ModeRequest(BaseModel):
    mode: str

@router.get("/state")
async def get_state():
    logger.info("Getting robot cleaner state")
    result = service.get_state()
    logger.info(f"Robot cleaner state: {result}")
    return result

@router.post("/state")
async def set_state(request: StateRequest):
    logger.info(f"Setting robot cleaner state to: {request.state}")
    result = service.set_state(request.state)
    if result["result"] == "fail":
        logger.error(f"Failed to set robot cleaner state: {result['msg']}")
        raise HTTPException(status_code=400, detail=result["msg"])
    logger.info(f"Successfully set robot cleaner state: {result}")
    return result

@router.get("/mode")
async def get_mode():
    logger.info("Getting robot cleaner mode")
    result = service.get_mode()
    logger.info(f"Robot cleaner mode: {result}")
    return result

@router.post("/mode")
async def set_mode(request: ModeRequest):
    logger.info(f"Setting robot cleaner mode to: {request.mode}")
    result = service.set_mode(request.mode)
    if result["result"] == "fail":
        logger.error(f"Failed to set robot cleaner mode: {result['msg']}")
        raise HTTPException(status_code=400, detail=result["msg"])
    logger.info(f"Successfully set robot cleaner mode: {result}")
    return result

@router.get("/mode/list")
async def get_mode_list():
    logger.info("Getting robot cleaner mode list")
    result = service.get_mode_list()
    logger.info(f"Robot cleaner mode list: {result}")
    return result

@router.get("/filter")
async def get_filter_used():
    logger.info("Getting robot cleaner filter usage")
    result = service.get_filter_used()
    logger.info(f"Robot cleaner filter usage: {result}")
    return result

@router.get("/cleaner-count")
async def get_cleaner_count():
    logger.info("Getting robot cleaner count")
    result = service.get_cleaner_count()
    logger.info(f"Robot cleaner count: {result}")
    return result
