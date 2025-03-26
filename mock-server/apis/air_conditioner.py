from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.air_conditioner_service import AirConditionerService
from logging_config import setup_logger

# 에어컨 API용 로거 설정
logger = setup_logger("air_conditioner_api")

router = APIRouter(prefix="/air-conditioner", tags=["air-conditioner"])
service = AirConditionerService()

class StateRequest(BaseModel):
    state: str

class ModeRequest(BaseModel):
    mode: str

@router.get("/state")
async def get_state():
    logger.info("Getting air conditioner state")
    result = service.get_state()
    logger.info(f"Air conditioner state: {result}")
    return result

@router.post("/state")
async def set_state(request: StateRequest):
    logger.info(f"Setting air conditioner state to: {request.state}")
    result = service.set_state(request.state)
    if result["result"] == "fail":
        logger.error(f"Failed to set air conditioner state: {result['msg']}")
        raise HTTPException(status_code=400, detail=result["msg"])
    logger.info(f"Successfully set air conditioner state: {result}")
    return result

@router.get("/mode")
async def get_mode():
    logger.info("Getting air conditioner mode")
    result = service.get_mode()
    logger.info(f"Air conditioner mode: {result}")
    return result

@router.post("/mode")
async def set_mode(request: ModeRequest):
    logger.info(f"Setting air conditioner mode to: {request.mode}")
    result = service.set_mode(request.mode)
    if result["result"] == "fail":
        logger.error(f"Failed to set air conditioner mode: {result['msg']}")
        raise HTTPException(status_code=400, detail=result["msg"])
    logger.info(f"Successfully set air conditioner mode: {result}")
    return result

@router.get("/mode/list")
async def get_mode_list():
    logger.info("Getting air conditioner mode list")
    result = service.get_mode_list()
    logger.info(f"Air conditioner mode list: {result}")
    return result

@router.get("/filter")
async def get_filter_used():
    logger.info("Getting air conditioner filter usage")
    result = service.get_filter_used()
    logger.info(f"Air conditioner filter usage: {result}")
    return result
