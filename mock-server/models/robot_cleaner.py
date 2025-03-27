from enum import Enum
import random
from typing import List

class RobotCleanerMode(str, Enum):
    NORMAL = "normal"
    PET = "pet"
    POWER = "power"
    AUTO = "auto"
    PATROL = "patrol"

class PatrolArea(str, Enum):
    LIVING_ROOM = "거실"
    MASTER_BEDROOM = "안방"
    KITCHEN = "부엌"
    SMALL_ROOM = "작은방"

class RobotCleaner:
    def __init__(self):
        self.state: str = "off"
        self.mode: RobotCleanerMode = RobotCleanerMode.NORMAL
        self.filter_used: int = random.randint(1, 100)
        self.cleaner_count: int = random.randint(1, 10)
        self.patrol_areas: List[str] = []
    
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
    
    def get_patrol_areas(self) -> List[str]:
        """설정된 방범 구역 목록을 반환합니다."""
        return self.patrol_areas
    
    def get_available_patrol_areas(self) -> List[str]:
        """설정 가능한 모든 방범 구역 목록을 반환합니다."""
        return [area.value for area in PatrolArea]
    
    def set_patrol_areas(self, areas: List[str]) -> bool:
        """방범 구역을 설정합니다. 유효한 구역만 설정할 수 있습니다."""
        valid_areas = self.get_available_patrol_areas()
        
        # 모든 요청 구역이 유효한지 확인
        for area in areas:
            if area not in valid_areas:
                return False
        
        # 유효한 구역만 설정
        self.patrol_areas = areas
        
        # 방범 모드가 아니면 자동으로 방범 모드로 변경
        if self.mode != RobotCleanerMode.PATROL:
            self.mode = RobotCleanerMode.PATROL
            
        return True
