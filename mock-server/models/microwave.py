from pydantic import BaseModel
from typing import Optional, List, Dict, Any, Union
from enum import Enum

class PowerState(str, Enum):
    ON = "on"
    OFF = "off"

class MicrowaveMode(str, Enum):
    MICROWAVE = "microwave"
    BAKING = "baking"
    GRILLING = "grilling"
    OVEN = "oven"

class MicrowaveState(BaseModel):
    """전자레인지 상태 모델"""
    power_state: PowerState = PowerState.OFF
    is_cooking: bool = False
    timer: Optional[int] = None
    timer_left: Optional[int] = None
    mode: MicrowaveMode = MicrowaveMode.MICROWAVE
    
class PowerStateRequest(BaseModel):
    """전자레인지 전원 상태 변경 요청 모델"""
    power_state: PowerState

class MicrowaveModeRequest(BaseModel):
    """전자레인지 모드 변경 요청 모델"""
    mode: str

class StepInfoRequest(BaseModel):
    """레시피 스텝 정보 요청 모델"""
    step_info: str

class CookingRequest(BaseModel):
    """전자레인지 조리 시작 요청 모델"""
    timer: int

class ResultResponse(BaseModel):
    """결과 응답 모델"""
    result: str
    message: Optional[str] = None

class ModeListResponse(BaseModel):
    """모드 목록 응답 모델"""
    modes: List[str] 