from models.refrigerator import (
    CookingState, ResultResponse
)
from typing import Dict, Optional
from logging_config import setup_logger

# 로거 설정
logger = setup_logger("refrigerator_service")

# 냉장고 상태 저장용 전역 변수
_cooking_state = CookingState.IDLE
_current_recipe_step = None

def get_cooking_state() -> Dict:
    """냉장고 디스플레이 요리 상태 조회"""
    logger.info(f"냉장고 디스플레이 요리 상태 조회: {_cooking_state}")
    return {"cooking_state": _cooking_state}

def set_cooking_state(step_info: str) -> ResultResponse:
    """냉장고 디스플레이에 레시피 스텝 정보 설정"""
    global _cooking_state, _current_recipe_step
    
    _cooking_state = CookingState.PROGRESS
    _current_recipe_step = step_info
    
    logger.info(f"냉장고 디스플레이에 레시피 스텝 정보 설정: {step_info}")
    return ResultResponse(result="success")

def get_current_recipe_step() -> Optional[str]:
    """현재 설정된 레시피 스텝 정보 조회"""
    return _current_recipe_step 