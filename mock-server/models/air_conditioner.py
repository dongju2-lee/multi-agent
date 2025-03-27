from enum import Enum
import random
from typing import List

class AirConditionerMode(str, Enum):
    NORMAL = "normal"
    COOLING = "cooling"
    QUIET = "quiet"
    DEHUMIDIFY = "dehumidify"

class AirConditioner:
    def __init__(self):
        self.state: str = "off"
        self.mode: AirConditionerMode = AirConditionerMode.NORMAL
        self.filter_used: int = random.randint(1, 100)
        self.temperature: int = 24  # 기본 온도는 24도
        self.min_temperature: int = 18  # 최소 설정 온도
        self.max_temperature: int = 30  # 최대 설정 온도
    
    def set_state(self, state: str) -> bool:
        if state not in ["on", "off"]:
            return False
        self.state = state
        return True
    
    def get_state(self) -> str:
        return self.state
    
    def set_mode(self, mode: str) -> bool:
        try:
            self.mode = AirConditionerMode(mode)
            return True
        except ValueError:
            return False
    
    def get_mode(self) -> str:
        return self.mode.value
    
    def get_available_modes(self) -> List[str]:
        return [mode.value for mode in AirConditionerMode]
    
    def get_filter_used(self) -> int:
        # 실제 구현에서는 필터 사용량을 계산하는 로직이 들어갈 수 있습니다
        # 여기서는 간단히 랜덤값을 반환합니다
        self.filter_used = random.randint(1, 100)
        return self.filter_used
    
    def get_temperature(self) -> int:
        """현재 설정된 온도를 반환합니다."""
        return self.temperature
    
    def get_temperature_range(self) -> dict:
        """설정 가능한 온도 범위를 반환합니다."""
        return {
            "min": self.min_temperature,
            "max": self.max_temperature,
            "current": self.temperature
        }
    
    def set_temperature(self, temperature: int) -> bool:
        """온도를 설정합니다. 유효한 범위 내에 있어야 합니다."""
        if self.min_temperature <= temperature <= self.max_temperature:
            self.temperature = temperature
            return True
        return False
    
    def increase_temperature(self) -> int:
        """온도를 1도 올립니다. 최대 온도를 초과할 수 없습니다."""
        if self.temperature < self.max_temperature:
            self.temperature += 1
        return self.temperature
    
    def decrease_temperature(self) -> int:
        """온도를 1도 내립니다. 최소 온도 미만으로 내려갈 수 없습니다."""
        if self.temperature > self.min_temperature:
            self.temperature -= 1
        return self.temperature
