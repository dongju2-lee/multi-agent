from models.routine import Routine
from typing import Dict, List, Optional
from logging_config import setup_logger

# 루틴 서비스용 로거 설정
logger = setup_logger("routine_service")

class RoutineService:
    def __init__(self):
        self.routine = Routine()
        logger.info("RoutineService initialized")
    
    def add_routine(self, routine_name: str, routine_flow: List[str]) -> Dict[str, str]:
        """새로운 루틴을 추가합니다."""
        logger.debug(f"Attempting to add routine: {routine_name}")
        
        # 루틴 이름이 비어있는지 확인
        if not routine_name or not routine_name.strip():
            logger.warning("Failed to add routine: Empty routine name")
            return {"result": "fail", "msg": "루틴 이름은 비워둘 수 없습니다"}
        
        # 루틴 흐름이 비어있는지 확인
        if not routine_flow or len(routine_flow) == 0:
            logger.warning("Failed to add routine: Empty routine flow")
            return {"result": "fail", "msg": "루틴 흐름은 최소 하나 이상의 단계가 필요합니다"}
        
        # 루틴 추가
        self.routine.add_routine(routine_name, routine_flow)
        logger.info(f"Successfully added routine: {routine_name} with {len(routine_flow)} steps")
        return {"result": "success"}
    
    def remove_routine(self, routine_name: str) -> Dict[str, str]:
        """지정된 이름의 루틴을 제거합니다."""
        logger.debug(f"Attempting to remove routine: {routine_name}")
        
        # 루틴 이름이 비어있는지 확인
        if not routine_name or not routine_name.strip():
            logger.warning("Failed to remove routine: Empty routine name")
            return {"result": "fail", "msg": "루틴 이름은 비워둘 수 없습니다"}
        
        # 루틴 제거
        if self.routine.remove_routine(routine_name):
            logger.info(f"Successfully removed routine: {routine_name}")
            return {"result": "success"}
        else:
            logger.warning(f"Failed to remove routine: {routine_name} - Not found")
            return {"result": "fail", "msg": f"'{routine_name}' 루틴을 찾을 수 없습니다"}
    
    def get_all_routines(self) -> Dict[str, Dict[str, List[str]]]:
        """모든 루틴 목록을 반환합니다."""
        logger.debug("Getting all routines")
        routines = self.routine.get_all_routines()
        logger.info(f"Retrieved {len(routines)} routines")
        return {"routines": routines}
    
    def get_routine(self, routine_name: str) -> Dict[str, Optional[List[str]]]:
        """지정된 이름의 루틴을 반환합니다."""
        logger.debug(f"Getting routine: {routine_name}")
        routine = self.routine.get_routine(routine_name)
        if routine:
            logger.info(f"Retrieved routine: {routine_name}")
            return {"routine": routine}
        else:
            logger.warning(f"Routine not found: {routine_name}")
            return {"routine": None} 