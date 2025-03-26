from enum import Enum
import random
from typing import List

class RobotCleanerMode(str, Enum):
    NORMAL = "normal"
    PET = "pet"
    POWER = "power"
    AUTO = "auto"

class RobotCleaner:
    def __init__(self):
        self.state: str = "off"
        self.mode: RobotCleanerMode = RobotCleanerMode.NORMAL
        self.filter_used: int = random.randint(1, 100)
        self.cleaner_count: int = random.randint(1, 10)
    
    def set_state(self, state: str) -> bool:
        if state not in ["on", "off"]:
            return False
        self.state = state
        return True
    
    def get_state(self) -> str:
        return self.state
    
    def set_mode(self, mode: str) -> bool:
        try:
            self.mode = RobotCleanerMode(mode)
            return True
        except ValueError:
            return False
    
    def get_mode(self) -> str:
        return self.mode.value
    
    def get_available_modes(self) -> List[str]:
        return [mode.value for mode in RobotCleanerMode]
    
    def get_filter_used(self) -> int:
        # 실제 구현에서는 필터 사용량을 계산하는 로직이 들어갈 수 있습니다
        # 여기서는 간단히 랜덤값을 반환합니다
        self.filter_used = random.randint(1, 100)
        return self.filter_used
    
    def get_cleaner_count(self) -> int:
        # 오늘 청소한 횟수를 반환합니다
        # 여기서는 간단히 랜덤값을 반환합니다
        self.cleaner_count = random.randint(1, 10)
        return self.cleaner_count
