from enum import Enum
from typing import List, Optional

class RefrigeratorMode(str, Enum):
    RAPID_COOLING = "rapid_cooling"
    POWER_SAVING = "power_saving"
    NORMAL = "normal"

class Refrigerator:
    def __init__(self):
        self.state: str = "off"
        self.mode: RefrigeratorMode = RefrigeratorMode.NORMAL
    
    def set_state(self, state: str) -> bool:
        if state not in ["on", "off"]:
            return False
        self.state = state
        return True
    
    def get_state(self) -> str:
        return self.state
    
    def set_mode(self, mode: str) -> bool:
        try:
            self.mode = RefrigeratorMode(mode)
            return True
        except ValueError:
            return False
    
    def get_mode(self) -> str:
        return self.mode.value
    
    def get_available_modes(self) -> List[str]:
        return [mode.value for mode in RefrigeratorMode]
