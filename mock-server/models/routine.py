from typing import List, Dict, Optional

class Routine:
    def __init__(self):
        # 루틴 목록을 저장하는 딕셔너리 (키: 루틴 이름, 값: 루틴 흐름 목록)
        self.routines: Dict[str, List[str]] = {}
    
    def add_routine(self, routine_name: str, routine_flow: List[str]) -> bool:
        """새로운 루틴을 추가합니다."""
        # 이미 존재하는 루틴 이름인 경우 덮어씁니다
        self.routines[routine_name] = routine_flow
        return True
    
    def remove_routine(self, routine_name: str) -> bool:
        """지정된 이름의 루틴을 제거합니다."""
        if routine_name in self.routines:
            del self.routines[routine_name]
            return True
        return False
    
    def get_routine(self, routine_name: str) -> Optional[List[str]]:
        """지정된 이름의 루틴 흐름을 반환합니다."""
        return self.routines.get(routine_name)
    
    def get_all_routines(self) -> Dict[str, List[str]]:
        """모든 루틴 목록을 반환합니다."""
        return self.routines
    
    def get_routine_names(self) -> List[str]:
        """모든 루틴 이름 목록을 반환합니다."""
        return list(self.routines.keys()) 