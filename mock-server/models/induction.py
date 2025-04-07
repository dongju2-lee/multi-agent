from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
from enum import Enum

class PowerState(str, Enum):
    ON = "on"
    OFF = "off"

class InductionState(BaseModel):
    """인덕션 상태 모델"""
    power_state: PowerState = PowerState.OFF
    is_cooking: bool = False
    timer: Optional[int] = None
    timer_left: Optional[int] = None
    
class PowerStateRequest(BaseModel):
    """인덕션 전원 상태 변경 요청 모델"""
    power_state: PowerState

class TimerRequest(BaseModel):
    """인덕션 타이머 설정 요청 모델"""
    timer: int

class ResultResponse(BaseModel):
    """결과 응답 모델"""
    result: str
    message: Optional[str] = None 