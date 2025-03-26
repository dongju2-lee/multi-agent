from models.air_conditioner import AirConditioner
from typing import Dict, List
from logging_config import setup_logger

# 에어컨 서비스용 로거 설정
logger = setup_logger("air_conditioner_service")

class AirConditionerService:
    def __init__(self):
        self.air_conditioner = AirConditioner()
        logger.info("AirConditionerService initialized")
    
    def get_state(self) -> Dict[str, str]:
        logger.debug("Getting air conditioner state")
        state = self.air_conditioner.get_state()
        return {"state": state}
    
    def set_state(self, state: str) -> Dict[str, str]:
        logger.debug(f"Attempting to set air conditioner state to: {state}")
        if self.air_conditioner.set_state(state):
            logger.debug(f"Successfully set air conditioner state to: {state}")
            return {"result": "success"}
        logger.warning(f"Failed to set air conditioner state to: {state} - Invalid state")
        return {"result": "fail", "msg": "유효하지 않은 상태입니다"}
    
    def get_mode(self) -> Dict[str, str]:
        logger.debug("Getting air conditioner mode")
        mode = self.air_conditioner.get_mode()
        return {"mode": mode}
    
    def set_mode(self, mode: str) -> Dict[str, str]:
        logger.debug(f"Attempting to set air conditioner mode to: {mode}")
        if self.air_conditioner.set_mode(mode):
            logger.debug(f"Successfully set air conditioner mode to: {mode}")
            return {"result": "success"}
        logger.warning(f"Failed to set air conditioner mode to: {mode} - Unsupported mode")
        return {"result": "fail", "msg": "지원하지 않는 mode입니다"}
    
    def get_mode_list(self) -> Dict[str, List[str]]:
        logger.debug("Getting available air conditioner modes")
        modes = self.air_conditioner.get_available_modes()
        return {"modes": modes}
    
    def get_filter_used(self) -> Dict[str, int]:
        logger.debug("Getting air conditioner filter usage")
        filter_used = self.air_conditioner.get_filter_used()
        logger.debug(f"Air conditioner filter usage: {filter_used}")
        return {"filter_used": filter_used}
