from fastapi import APIRouter, HTTPException
from models.induction import PowerState, PowerStateRequest, TimerRequest, ResultResponse
from services import induction_service
from logging_config import setup_logger

# 로거 설정
logger = setup_logger("induction_api")

router = APIRouter(
    prefix="/induction",
    tags=["induction"],
    responses={404: {"description": "Not found"}},
)

@router.get("/power/state", response_model=dict)
async def get_power_state():
    """인덕션 전원 상태 조회"""
    logger.info("API 호출: 인덕션 전원 상태 조회")
    return induction_service.get_power_state()

@router.post("/power/state", response_model=ResultResponse)
async def set_power_state(request: PowerStateRequest):
    """인덕션 전원 상태 변경"""
    logger.info(f"API 호출: 인덕션 전원 상태 변경 ({request.power_state})")
    return induction_service.set_power_state(request.power_state)

@router.post("/start-cooking", response_model=ResultResponse)
async def start_cooking(request: TimerRequest):
    """인덕션 조리 시작 및 타이머 설정"""
    logger.info(f"API 호출: 인덕션 조리 시작 (타이머: {request.timer}초)")
    return induction_service.start_cooking(request.timer) 