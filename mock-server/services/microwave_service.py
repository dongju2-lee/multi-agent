from models.microwave import PowerState, MicrowaveState, MicrowaveMode, ResultResponse, ModeListResponse
from typing import Dict, Optional, List
import time
from logging_config import setup_logger

# 로거 설정
logger = setup_logger("microwave_service")

# 전자레인지 상태 저장용 전역 변수
_microwave_state = MicrowaveState()
_current_step_info = None

def get_power_state() -> Dict:
    """전자레인지 전원 상태 조회"""
    logger.info(f"전자레인지 전원 상태 조회: {_microwave_state.power_state}")
    return {"power_state": _microwave_state.power_state}

def set_power_state(power_state: PowerState) -> ResultResponse:
    """전자레인지 전원 상태 변경"""
    global _microwave_state
    
    # 현재 상태와 동일하면 바로 성공 반환
    if _microwave_state.power_state == power_state:
        logger.info(f"전자레인지 전원 상태 변경 불필요 (현재 상태: {power_state})")
        return ResultResponse(result="success", message=f"이미 {power_state} 상태입니다.")
    
    # 상태 변경
    _microwave_state.power_state = power_state
    
    # 전원이 꺼지면 모든 조리 활동 중지
    if power_state == PowerState.OFF:
        _microwave_state.is_cooking = False
        _microwave_state.timer = None
        _microwave_state.timer_left = None
        logger.info("전자레인지 전원 OFF, 모든 조리 활동 중지")
    
    logger.info(f"전자레인지 전원 상태 변경 성공: {power_state}")
    return ResultResponse(result="success")

def get_mode() -> Dict:
    """전자레인지 모드 조회"""
    logger.info(f"전자레인지 모드 조회: {_microwave_state.mode}")
    return {"mode": _microwave_state.mode}

def get_mode_list() -> ModeListResponse:
    """전자레인지 가능한 모드 목록 조회"""
    modes = [mode.value for mode in MicrowaveMode]
    logger.info(f"전자레인지 가능한 모드 목록 조회: {modes}")
    return ModeListResponse(modes=modes)

def set_mode(mode_str: str) -> ResultResponse:
    """전자레인지 모드 변경"""
    global _microwave_state
    
    # 전원이 꺼져 있으면 모드 변경 불가
    if _microwave_state.power_state == PowerState.OFF:
        logger.warning("전자레인지 모드 변경 실패: 전원이 꺼져 있음")
        return ResultResponse(
            result="fail",
            message="전자레인지 전원이 꺼져 있습니다. 먼저 전원을 켜야 합니다."
        )
    
    # 모드 유효성 검사
    try:
        new_mode = MicrowaveMode(mode_str.lower())
    except ValueError:
        available_modes = [mode.value for mode in MicrowaveMode]
        logger.warning(f"전자레인지 모드 변경 실패: 유효하지 않은 모드 ({mode_str})")
        return ResultResponse(
            result="fail",
            message=f"'{mode_str}'은(는) 유효한 모드가 아닙니다. 가능한 모드: {', '.join(available_modes)}"
        )
    
    # 현재 모드와 동일하면 바로 성공 반환
    if _microwave_state.mode == new_mode:
        logger.info(f"전자레인지 모드 변경 불필요 (현재 모드: {new_mode})")
        return ResultResponse(result="success", message=f"이미 {new_mode} 모드입니다.")
    
    # 모드 변경
    _microwave_state.mode = new_mode
    logger.info(f"전자레인지 모드 변경 성공: {new_mode}")
    return ResultResponse(result="success")

def set_step_info(step_info: str) -> ResultResponse:
    """레시피 스텝 정보 설정"""
    global _current_step_info
    
    _current_step_info = step_info
    logger.info(f"전자레인지 레시피 스텝 정보 설정: {step_info}")
    return ResultResponse(result="success")

def start_cooking(timer: int) -> ResultResponse:
    """전자레인지 조리 시작 및 타이머 설정"""
    global _microwave_state
    
    # 전원이 꺼져 있으면 실패 처리
    if _microwave_state.power_state == PowerState.OFF:
        logger.warning("전자레인지 조리 시작 실패: 전원이 꺼져 있음")
        return ResultResponse(
            result="fail",
            message="전자레인지 전원이 꺼져 있습니다. 먼저 전원을 켜야 합니다."
        )
    
    # 타이머 값 검증
    if timer <= 0:
        logger.warning(f"전자레인지 조리 시작 실패: 잘못된 타이머 값 ({timer})")
        return ResultResponse(
            result="fail", 
            message="타이머 값은 0보다 커야 합니다."
        )
    
    # 타이머 설정 및 조리 시작
    _microwave_state.timer = timer
    _microwave_state.timer_left = timer
    _microwave_state.is_cooking = True
    
    logger.info(f"전자레인지 조리 시작 (타이머: {timer}초, 모드: {_microwave_state.mode})")
    return ResultResponse(result="success")

def get_current_step_info() -> Optional[str]:
    """현재 설정된 레시피 스텝 정보 조회"""
    return _current_step_info 