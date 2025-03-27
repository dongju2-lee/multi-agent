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

class TemperatureRequest(BaseModel):
    temperature: int

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

# 추가된 온도 관련 API 엔드포인트

@router.get("/temperature")
async def get_temperature():
    """현재 설정된 에어컨 온도를 조회합니다."""
    logger.info("Getting air conditioner temperature")
    result = service.get_temperature()
    logger.info(f"Air conditioner temperature: {result}")
    return result

@router.get("/temperature/range")
async def get_temperature_range():
    """에어컨의 온도 설정 범위를 조회합니다."""
    logger.info("Getting air conditioner temperature range")
    result = service.get_temperature_range()
    logger.info(f"Air conditioner temperature range: {result}")
    return result

@router.post("/temperature")
async def set_temperature(request: TemperatureRequest):
    """에어컨의 온도를 설정합니다."""
    logger.info(f"Setting air conditioner temperature to: {request.temperature}")
    result = service.set_temperature(request.temperature)
    if result["result"] == "fail":
        logger.error(f"Failed to set air conditioner temperature: {result['msg']}")
        raise HTTPException(status_code=400, detail=result["msg"])
    logger.info(f"Successfully set air conditioner temperature: {result}")
    return result

@router.post("/temperature/increase")
async def increase_temperature():
    """에어컨의 온도를 1도 올립니다."""
    logger.info("Increasing air conditioner temperature")
    result = service.increase_temperature()
    logger.info(f"Air conditioner temperature increased to: {result}")
    return result

@router.post("/temperature/decrease")
async def decrease_temperature():
    """에어컨의 온도를 1도 내립니다."""
    logger.info("Decreasing air conditioner temperature")
    result = service.decrease_temperature()
    logger.info(f"Air conditioner temperature decreased to: {result}")
    return result
