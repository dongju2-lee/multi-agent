from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.refrigerator_service import RefrigeratorService
from typing import List
from logging_config import setup_logger

# 냉장고 API용 로거 설정
logger = setup_logger("refrigerator_api")

router = APIRouter(prefix="/refrigerator", tags=["refrigerator"])
service = RefrigeratorService()

class StateRequest(BaseModel):
    state: str

class ModeRequest(BaseModel):
    mode: str

@router.get("/state")
async def get_state():
    logger.info("Getting refrigerator state")
    result = service.get_state()
    logger.info(f"Refrigerator state: {result}")
    return result

@router.post("/state")
async def set_state(request: StateRequest):
    logger.info(f"Setting refrigerator state to: {request.state}")
    result = service.set_state(request.state)
    if result["result"] == "fail":
        logger.error(f"Failed to set refrigerator state: {result['msg']}")
        raise HTTPException(status_code=400, detail=result["msg"])
    logger.info(f"Successfully set refrigerator state: {result}")
    return result

@router.get("/mode")
async def get_mode():
    logger.info("Getting refrigerator mode")
    result = service.get_mode()
    logger.info(f"Refrigerator mode: {result}")
    return result

@router.post("/mode")
async def set_mode(request: ModeRequest):
    logger.info(f"Setting refrigerator mode to: {request.mode}")
    result = service.set_mode(request.mode)
    if result["result"] == "fail":
        logger.error(f"Failed to set refrigerator mode: {result['msg']}")
        raise HTTPException(status_code=400, detail=result["msg"])
    logger.info(f"Successfully set refrigerator mode: {result}")
    return result

@router.get("/mode/list")
async def get_mode_list():
    logger.info("Getting refrigerator mode list")
    result = service.get_mode_list()
    logger.info(f"Refrigerator mode list: {result}")
    return result

@router.get("/food")
async def get_food_list():
    logger.info("Getting refrigerator food list")
    result = service.get_food_list()
    logger.info(f"Refrigerator food list: {result}")
    return result
