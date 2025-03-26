from models.refrigerator import Refrigerator
from models.food_list import get_random_foods
from typing import Dict, List, Union
from logging_config import setup_logger

# 냉장고 서비스용 로거 설정
logger = setup_logger("refrigerator_service")

class RefrigeratorService:
    def __init__(self):
        self.refrigerator = Refrigerator()
        logger.info("RefrigeratorService initialized")
    
    def get_state(self) -> Dict[str, str]:
        logger.debug("Getting refrigerator state")
        state = self.refrigerator.get_state()
        return {"state": state}
    
    def set_state(self, state: str) -> Dict[str, str]:
        logger.debug(f"Attempting to set refrigerator state to: {state}")
        if self.refrigerator.set_state(state):
            logger.debug(f"Successfully set refrigerator state to: {state}")
            return {"result": "success"}
        logger.warning(f"Failed to set refrigerator state to: {state} - Invalid state")
        return {"result": "fail", "msg": "유효하지 않은 상태입니다"}
    
    def get_mode(self) -> Dict[str, str]:
        logger.debug("Getting refrigerator mode")
        mode = self.refrigerator.get_mode()
        return {"mode": mode}
    
    def set_mode(self, mode: str) -> Dict[str, str]:
        logger.debug(f"Attempting to set refrigerator mode to: {mode}")
        if self.refrigerator.set_mode(mode):
            logger.debug(f"Successfully set refrigerator mode to: {mode}")
            return {"result": "success"}
        logger.warning(f"Failed to set refrigerator mode to: {mode} - Unsupported mode")
        return {"result": "fail", "msg": "지원하지 않는 mode입니다"}
    
    def get_mode_list(self) -> Dict[str, List[str]]:
        logger.debug("Getting available refrigerator modes")
        modes = self.refrigerator.get_available_modes()
        return {"modes": modes}
    
    def get_food_list(self) -> Dict[str, List[str]]:
        logger.debug("Getting random food list from refrigerator")
        foods = get_random_foods()
        logger.debug(f"Retrieved {len(foods)} food items")
        return {"foods": foods}
