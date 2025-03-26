from models.robot_cleaner import RobotCleaner
from typing import Dict, List
from logging_config import setup_logger

# 로봇청소기 서비스용 로거 설정
logger = setup_logger("robot_cleaner_service")

class RobotCleanerService:
    def __init__(self):
        self.robot_cleaner = RobotCleaner()
        logger.info("RobotCleanerService initialized")
    
    def get_state(self) -> Dict[str, str]:
        logger.debug("Getting robot cleaner state")
        state = self.robot_cleaner.get_state()
        return {"state": state}
    
    def set_state(self, state: str) -> Dict[str, str]:
        logger.debug(f"Attempting to set robot cleaner state to: {state}")
        if self.robot_cleaner.set_state(state):
            logger.debug(f"Successfully set robot cleaner state to: {state}")
            return {"result": "success"}
        logger.warning(f"Failed to set robot cleaner state to: {state} - Invalid state")
        return {"result": "fail", "msg": "유효하지 않은 상태입니다"}
    
    def get_mode(self) -> Dict[str, str]:
        logger.debug("Getting robot cleaner mode")
        mode = self.robot_cleaner.get_mode()
        return {"mode": mode}
    
    def set_mode(self, mode: str) -> Dict[str, str]:
        logger.debug(f"Attempting to set robot cleaner mode to: {mode}")
        if self.robot_cleaner.set_mode(mode):
            logger.debug(f"Successfully set robot cleaner mode to: {mode}")
            return {"result": "success"}
        logger.warning(f"Failed to set robot cleaner mode to: {mode} - Unsupported mode")
        return {"result": "fail", "msg": "지원하지 않는 mode입니다"}
    
    def get_mode_list(self) -> Dict[str, List[str]]:
        logger.debug("Getting available robot cleaner modes")
        modes = self.robot_cleaner.get_available_modes()
        return {"modes": modes}
    
    def get_filter_used(self) -> Dict[str, int]:
        logger.debug("Getting robot cleaner filter usage")
        filter_used = self.robot_cleaner.get_filter_used()
        logger.debug(f"Robot cleaner filter usage: {filter_used}")
        return {"filter_used": filter_used}
    
    def get_cleaner_count(self) -> Dict[str, int]:
        logger.debug("Getting robot cleaner count")
        cleaner_count = self.robot_cleaner.get_cleaner_count()
        logger.debug(f"Robot cleaner count: {cleaner_count}")
        return {"cleaner_count": cleaner_count}
