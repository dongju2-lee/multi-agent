from fastapi import APIRouter, HTTPException
from models.microwave import PowerState, PowerStateRequest, StepInfoRequest, CookingRequest, MicrowaveModeRequest, ResultResponse, ModeListResponse
from services import microwave_service
from logging_config import setup_logger

# 로거 설정
logger = setup_logger("microwave_api")

router = APIRouter(
    prefix="/microwave",
    tags=["Microwave"],
    responses={404: {"description": "Not found"}},
)

@router.get("/power/state", response_model=dict)
async def get_power_state():
    """전자레인지 전원 상태 조회"""
    logger.info("API 호출: 전자레인지 전원 상태 조회")
    return microwave_service.get_power_state()

@router.post("/power/state", response_model=ResultResponse)
async def set_power_state(request: PowerStateRequest):
    """전자레인지 전원 상태 변경"""
    logger.info(f"API 호출: 전자레인지 전원 상태 변경 ({request.power_state})")
    return microwave_service.set_power_state(request.power_state)

@router.get("/mode", response_model=dict)
async def get_mode():
    """전자레인지 모드 조회"""
    logger.info("API 호출: 전자레인지 모드 조회")
    return microwave_service.get_mode()

@router.get("/mode/list", response_model=ModeListResponse)
async def get_mode_list():
    """전자레인지 가능한 모드 목록 조회"""
    logger.info("API 호출: 전자레인지 가능한 모드 목록 조회")
    return microwave_service.get_mode_list()

@router.post("/mode", response_model=ResultResponse)
async def set_mode(request: MicrowaveModeRequest):
    """전자레인지 모드 변경"""
    logger.info(f"API 호출: 전자레인지 모드 변경 ({request.mode})")
    return microwave_service.set_mode(request.mode)

@router.post("/step-info", response_model=ResultResponse)
async def set_step_info(request: StepInfoRequest):
    """전자레인지에 레시피 스텝 정보 설정"""
    logger.info(f"API 호출: 전자레인지 레시피 스텝 정보 설정")
    return microwave_service.set_step_info(request.step_info)

@router.post("/start-cooking", response_model=ResultResponse)
async def start_cooking(request: CookingRequest):
    """전자레인지 조리 시작 및 타이머 설정"""
    logger.info(f"API 호출: 전자레인지 조리 시작 (타이머: {request.timer}초)")
    return microwave_service.start_cooking(request.timer) 