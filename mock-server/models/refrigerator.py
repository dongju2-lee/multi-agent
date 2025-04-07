from pydantic import BaseModel
from typing import Optional
from enum import Enum

class CookingState(str, Enum):
    PROGRESS = "progress"
    IDLE = "idle"

class CookingStateResponse(BaseModel):
    """요리 상태 응답 모델"""
    cooking_state: CookingState

class StepInfoRequest(BaseModel):
    """레시피 스텝 정보 요청 모델"""
    step_info: str

class ResultResponse(BaseModel):
    """결과 응답 모델"""
    result: str
    message: Optional[str] = None 