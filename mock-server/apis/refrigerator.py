from fastapi import APIRouter, HTTPException
from models.refrigerator import (
    CookingStateResponse, StepInfoRequest, ResultResponse
)
from services import refrigerator_service
from logging_config import setup_logger

# 로거 설정
logger = setup_logger("refrigerator_api")

router = APIRouter(
    prefix="/refrigerator",
    tags=["Refrigerator"],
    responses={404: {"description": "Not found"}},
)

@router.get("/cooking-state", response_model=dict)
async def get_cooking_state():
    """냉장고 디스플레이 요리 상태 조회"""
    logger.info("API 호출: 냉장고 디스플레이 요리 상태 조회")
    return refrigerator_service.get_cooking_state()

@router.post("/cooking-state", response_model=ResultResponse)
async def set_cooking_state(request: StepInfoRequest):
    """냉장고 디스플레이에 레시피 스텝 정보 설정"""
    logger.info(f"API 호출: 냉장고 디스플레이에 레시피 스텝 정보 설정")
    return refrigerator_service.set_cooking_state(request.step_info) 