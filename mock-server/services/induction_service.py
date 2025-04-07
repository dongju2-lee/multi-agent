from models.induction import PowerState, InductionState, ResultResponse
from typing import Dict, Optional
import time
from logging_config import setup_logger

# 로거 설정
logger = setup_logger("induction_service")

# 인덕션 상태 저장용 전역 변수
_induction_state = InductionState()

def get_power_state() -> Dict:
    """인덕션 전원 상태 조회"""
    logger.info(f"인덕션 전원 상태 조회: {_induction_state.power_state}")
    return {"power_state": _induction_state.power_state}

def set_power_state(power_state: PowerState) -> ResultResponse:
    """인덕션 전원 상태 변경"""
    global _induction_state
    
    # 현재 상태와 동일하면 바로 성공 반환
    if _induction_state.power_state == power_state:
        logger.info(f"인덕션 전원 상태 변경 불필요 (현재 상태: {power_state})")
        return ResultResponse(result="success", message=f"이미 {power_state} 상태입니다.")
    
    # 상태 변경
    _induction_state.power_state = power_state
    
    # 전원이 꺼지면 모든 조리 활동 중지
    if power_state == PowerState.OFF:
        _induction_state.is_cooking = False
        _induction_state.timer = None
        _induction_state.timer_left = None
        logger.info("인덕션 전원 OFF, 모든 조리 활동 중지")
    
    logger.info(f"인덕션 전원 상태 변경 성공: {power_state}")
    return ResultResponse(result="success")

def start_cooking(timer: int) -> ResultResponse:
    """인덕션 조리 시작 및 타이머 설정"""
    global _induction_state
    
    # 전원이 꺼져 있으면 실패 처리
    if _induction_state.power_state == PowerState.OFF:
        logger.warning("인덕션 조리 시작 실패: 전원이 꺼져 있음")
        return ResultResponse(
            result="fail",
            message="인덕션 전원이 꺼져 있습니다. 먼저 전원을 켜야 합니다."
        )
    
    # 타이머 값 검증
    if timer <= 0:
        logger.warning(f"인덕션 조리 시작 실패: 잘못된 타이머 값 ({timer})")
        return ResultResponse(
            result="fail", 
            message="타이머 값은 0보다 커야 합니다."
        )
    
    # 타이머 설정 및 조리 시작
    _induction_state.timer = timer
    _induction_state.timer_left = timer
    _induction_state.is_cooking = True
    
    logger.info(f"인덕션 조리 시작 (타이머: {timer}초)")
    return ResultResponse(result="success") 