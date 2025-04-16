from models.brain import (
    BrainState, Activity, TaskContext, PausedTask, TodoItem,
    BrainResponse, BrainUpdateRequest, BrainAddRequest, BrainDeleteRequest
)
from typing import Dict, List, Any, Optional
from datetime import datetime
import json
import os
from logging_config import setup_logger
import traceback

# 로거 설정
logger = setup_logger("brain_service")

class BrainService:
    def __init__(self):
        # 브레인 상태 초기화
        self.brain_state = BrainState()
        
        # 브레인 상태 저장 파일 경로
        self.brain_file = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "brain_store",
            "brain_state.json"
        )
        
        # 브레인 저장 디렉토리 생성
        brain_dir = os.path.dirname(self.brain_file)
        os.makedirs(brain_dir, exist_ok=True)
        
        # 기존 브레인 상태 불러오기 시도
        self._load_brain_state()
        
        # 브레인 상태가 비어있으면 기본값 설정
        if not self._has_data():
            self._setup_default_brain_state()
            self._save_brain_state()
        
        logger.info("BrainService initialized")
    
    def _has_data(self) -> bool:
        """브레인 상태에 데이터가 있는지 확인"""
        return (
            len(self.brain_state.daily_activities) > 0 or
            len(self.brain_state.today_activities) > 0 or
            self.brain_state.current_task is not None or
            len(self.brain_state.paused_tasks) > 0 or
            len(self.brain_state.todo_list) > 0
        )
    
    def _setup_default_brain_state(self):
        """기본 브레인 상태 설정"""
        now_iso = datetime.now().isoformat()
        yesterday_iso = datetime.now().replace(day=datetime.now().day-1).isoformat()
        
        # 일일 활동 예제
        self.brain_state.daily_activities = [
            Activity(
                time="2025-04-02", 
                session_id="session-yesterday", 
                summary="오늘 고기 샌드위치 요리법을 알려달라고 했던 대화"
            )
        ]
        
        # 오늘 활동 예제
        self.brain_state.today_activities = [
            Activity(
                time="08:30:15", 
                session_id="morning-session", 
                summary="오늘의 날씨를 물어봤던 대화"
            )
        ]
        
        # 할 일 목록 예제
        self.brain_state.todo_list = [
            TodoItem(
                request_time=now_iso, 
                session_id="todo-session-1", 
                summary="오늘 저녁 8시에 운동하기"
            ),
            TodoItem(
                request_time=now_iso, 
                session_id="todo-session-2", 
                summary="내일 점심으로 비빔밥 해먹기"
            )
        ]
        
        logger.info("Default brain state set up")
    
    def _load_brain_state(self):
        """파일에서 브레인 상태 로드"""
        try:
            if os.path.exists(self.brain_file):
                with open(self.brain_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # JSON에서 BrainState 객체로 변환
                self.brain_state = BrainState.parse_obj(data)
                logger.info("Brain state loaded from file")
                
        except Exception as e:
            logger.error(f"Error loading brain state: {str(e)}")
            logger.error(traceback.format_exc())
            # 오류 발생 시 새로운 브레인 상태 사용
            self.brain_state = BrainState()
    
    def _save_brain_state(self):
        """브레인 상태를 파일에 저장"""
        try:
            with open(self.brain_file, 'w', encoding='utf-8') as f:
                json.dump(self.brain_state.dict(), f, ensure_ascii=False, indent=2)
            logger.info("Brain state saved to file")
            
        except Exception as e:
            logger.error(f"Error saving brain state: {str(e)}")
            logger.error(traceback.format_exc())
    
    def get_brain_state(self) -> Dict[str, Any]:
        """전체 브레인 상태 조회"""
        logger.info("Getting full brain state")
        return {
            "result": "success",
            "data": self.brain_state.dict()
        }
    
    def _get_value_by_path(self, path: str) -> Any:
        """주어진 경로에 해당하는 값 조회
        
        이제 배열 인덱스 처리 없이 키만으로 접근하며, 배열 전체를 반환합니다.
        """
        # 경로가 비어있으면 전체 상태 반환
        if not path:
            return self.brain_state.dict()
        
        # 만약 경로에 배열 인덱스가 포함되어 있다면 경고 로그를 남기고 배열 전체를 반환
        if '[' in path and path.endswith(']'):
            array_name = path.split('[')[0]
            logger.warning(f"배열 인덱스 접근이 요청되었습니다: {path}. 대신 {array_name} 전체를 반환합니다.")
            return self._get_value_by_key(array_name)
        
        return self._get_value_by_key(path)
    
    def _get_value_by_key(self, key: str) -> Any:
        """단일 키로 값을 조회합니다."""
        current = self.brain_state.dict()
        
        # 점(.)으로 구분된 중첩 키 처리
        if '.' in key:
            parts = key.split('.')
            for part in parts:
                if part in current:
                    current = current[part]
                else:
                    raise KeyError(f"Key {part} not found")
            return current
        
        # 단일 키 처리
        if key in current:
            return current[key]
        else:
            raise KeyError(f"Key {key} not found")
    
    def _set_value_by_path(self, path: str, value: Any):
        """주어진 경로에 값 설정"""
        parts = path.split('.')
        target = self.brain_state.dict()
        temp_target = target
        
        # 마지막 부분을 제외한 경로 탐색
        for i, part in enumerate(parts[:-1]):
            # 배열 인덱스 처리
            if '[' in part and part.endswith(']'):
                array_name, idx_str = part.split('[')
                idx = int(idx_str[:-1])
                
                if array_name in temp_target:
                    if 0 <= idx < len(temp_target[array_name]):
                        temp_target = temp_target[array_name][idx]
                    else:
                        raise IndexError(f"Index {idx} out of range for {array_name}")
                else:
                    raise KeyError(f"Key {array_name} not found")
            else:
                if part in temp_target:
                    temp_target = temp_target[part]
                else:
                    raise KeyError(f"Key {part} not found")
        
        # 마지막 부분에 값 설정
        last_part = parts[-1]
        
        # 배열 인덱스 처리
        if '[' in last_part and last_part.endswith(']'):
            array_name, idx_str = last_part.split('[')
            idx = int(idx_str[:-1])
            
            if array_name in temp_target:
                if 0 <= idx < len(temp_target[array_name]):
                    temp_target[array_name][idx] = value
                else:
                    raise IndexError(f"Index {idx} out of range for {array_name}")
            else:
                raise KeyError(f"Key {array_name} not found")
        else:
            if last_part in temp_target:
                temp_target[last_part] = value
            else:
                raise KeyError(f"Key {last_part} not found")
        
        # 변경된 사전을 BrainState로 변환하여 설정
        self.brain_state = BrainState.parse_obj(target)
    
    def _delete_value_by_path(self, path: str):
        """주어진 경로의 값 삭제"""
        parts = path.split('.')
        target = self.brain_state.dict()
        temp_target = target
        
        # 마지막 부분을 제외한 경로 탐색
        for i, part in enumerate(parts[:-1]):
            # 배열 인덱스 처리
            if '[' in part and part.endswith(']'):
                array_name, idx_str = part.split('[')
                idx = int(idx_str[:-1])
                
                if array_name in temp_target:
                    if 0 <= idx < len(temp_target[array_name]):
                        temp_target = temp_target[array_name][idx]
                    else:
                        raise IndexError(f"Index {idx} out of range for {array_name}")
                else:
                    raise KeyError(f"Key {array_name} not found")
            else:
                if part in temp_target:
                    temp_target = temp_target[part]
                else:
                    raise KeyError(f"Key {part} not found")
        
        # 마지막 부분 삭제
        last_part = parts[-1]
        
        # 배열 인덱스 처리
        if '[' in last_part and last_part.endswith(']'):
            array_name, idx_str = last_part.split('[')
            idx = int(idx_str[:-1])
            
            if array_name in temp_target:
                if 0 <= idx < len(temp_target[array_name]):
                    temp_target[array_name].pop(idx)
                else:
                    raise IndexError(f"Index {idx} out of range for {array_name}")
            else:
                raise KeyError(f"Key {array_name} not found")
        else:
            if last_part in temp_target:
                del temp_target[last_part]
            else:
                raise KeyError(f"Key {last_part} not found")
        
        # 변경된 사전을 BrainState로 변환하여 설정
        self.brain_state = BrainState.parse_obj(target)
    
    def get_by_path(self, path: str) -> Dict[str, Any]:
        """경로로 브레인 상태의 특정 부분 조회"""
        try:
            logger.info(f"Getting brain state value at path: {path}")
            value = self._get_value_by_path(path)
            return {
                "result": "success",
                "data": value
            }
        except (KeyError, IndexError) as e:
            logger.error(f"Error getting value at path {path}: {str(e)}")
            return {
                "result": "error",
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error getting value at path {path}: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "result": "error",
                "message": f"Unexpected error: {str(e)}"
            }
    
    def update_brain(self, update_request: BrainUpdateRequest) -> Dict[str, str]:
        """브레인 상태 업데이트"""
        try:
            logger.info(f"Updating brain state at path: {update_request.path}")
            self._set_value_by_path(update_request.path, update_request.value)
            self._save_brain_state()
            
            return {
                "result": "success",
                "message": f"Updated value at {update_request.path}"
            }
        except (KeyError, IndexError) as e:
            logger.error(f"Error updating value at path {update_request.path}: {str(e)}")
            return {
                "result": "error",
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error updating value at path {update_request.path}: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "result": "error",
                "message": f"Unexpected error: {str(e)}"
            }
    
    def add_item(self, add_request: BrainAddRequest) -> Dict[str, str]:
        """컬렉션에 항목 추가"""
        try:
            collection = add_request.collection
            item = add_request.item
            logger.info(f"Adding item to collection: {collection}")
            
            if collection == "daily_activities":
                self.brain_state.daily_activities.append(Activity(**item))
            elif collection == "today_activities":
                self.brain_state.today_activities.append(Activity(**item))
            elif collection == "paused_tasks":
                self.brain_state.paused_tasks.append(PausedTask(**item))
            elif collection == "todo_list":
                self.brain_state.todo_list.append(TodoItem(**item))
            else:
                return {
                    "result": "error",
                    "message": f"Unknown collection: {collection}"
                }
            
            self._save_brain_state()
            
            return {
                "result": "success",
                "message": f"Added item to {collection}"
            }
        except Exception as e:
            logger.error(f"Error adding item to {add_request.collection}: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "result": "error",
                "message": f"Error: {str(e)}"
            }
    
    def delete_by_path(self, delete_request: BrainDeleteRequest) -> Dict[str, str]:
        """경로로 항목 삭제"""
        try:
            path = delete_request.path
            logger.info(f"Deleting item at path: {path}")
            
            self._delete_value_by_path(path)
            self._save_brain_state()
            
            return {
                "result": "success",
                "message": f"Deleted item at {path}"
            }
        except (KeyError, IndexError) as e:
            logger.error(f"Error deleting item at path {path}: {str(e)}")
            return {
                "result": "error",
                "message": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error deleting item at path {path}: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "result": "error",
                "message": f"Unexpected error: {str(e)}"
            }
    
    def set_current_task(self, task_data: Dict[str, Any]) -> Dict[str, str]:
        """현재 작업 설정"""
        try:
            logger.info("Setting current task")
            
            # 현재 작업 설정
            task_context = TaskContext(**task_data)
            self.brain_state.current_task = task_context
            
            # 작업 매니저와 함께 일하고 있음을 표시
            self.brain_state.working_with_manager = True
            
            self._save_brain_state()
            
            return {
                "result": "success",
                "message": "Current task set successfully"
            }
        except Exception as e:
            logger.error(f"Error setting current task: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "result": "error",
                "message": f"Error: {str(e)}"
            }
    
    def reset_current_task(self) -> Dict[str, str]:
        """현재 작업 초기화"""
        try:
            logger.info("Resetting current task")
            
            # 현재 작업 초기화
            self.brain_state.current_task = None
            
            # 작업 매니저와 함께 일하지 않음을 표시
            self.brain_state.working_with_manager = False
            
            self._save_brain_state()
            
            return {
                "result": "success",
                "message": "Current task reset successfully"
            }
        except Exception as e:
            logger.error(f"Error resetting current task: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "result": "error",
                "message": f"Error: {str(e)}"
            }
    
    def pause_current_task(self, summary: str) -> Dict[str, str]:
        """현재 작업 일시 중지 및 보관"""
        try:
            logger.info("Pausing current task")
            
            if not self.brain_state.current_task:
                return {
                    "result": "error",
                    "message": "No current task to pause"
                }
            
            # 현재 시간을 ISO 형식으로 가져오기
            now_iso = datetime.now().isoformat()
            
            # 현재 작업 복사
            current_task = self.brain_state.current_task.copy()
            
            # 일시 중지 시간 설정
            current_task.pause_time = now_iso
            
            # 일시 중지된 작업 목록에 추가
            paused_task = PausedTask(
                time=datetime.now().strftime("%H:%M:%S"),
                session_id=current_task.session_id,
                summary=summary,
                task_context=current_task
            )
            
            self.brain_state.paused_tasks.append(paused_task)
            
            # 현재 작업 초기화
            self.brain_state.current_task = None
            self.brain_state.working_with_manager = False
            
            self._save_brain_state()
            
            return {
                "result": "success",
                "message": "Current task paused successfully"
            }
        except Exception as e:
            logger.error(f"Error pausing current task: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "result": "error",
                "message": f"Error: {str(e)}"
            }
    
    def resume_task(self, paused_task_index: int) -> Dict[str, Any]:
        """일시 중지된 작업 재개"""
        try:
            logger.info(f"Resuming paused task at index: {paused_task_index}")
            
            if not 0 <= paused_task_index < len(self.brain_state.paused_tasks):
                return {
                    "result": "error",
                    "message": f"Paused task index {paused_task_index} is out of range"
                }
            
            # 현재 작업이 있으면 먼저 중지
            if self.brain_state.current_task:
                return {
                    "result": "error",
                    "message": "Cannot resume task while another task is in progress"
                }
            
            # 일시 중지된 작업 가져오기
            paused_task = self.brain_state.paused_tasks[paused_task_index]
            
            # 현재 작업으로 설정
            task_context = paused_task.task_context.copy()
            task_context.pause_time = None  # 일시 중지 시간 초기화
            task_context.last_updated = datetime.now().isoformat()  # 마지막 업데이트 시간 설정
            
            self.brain_state.current_task = task_context
            self.brain_state.working_with_manager = True
            
            # 일시 중지된 작업 목록에서 제거
            self.brain_state.paused_tasks.pop(paused_task_index)
            
            self._save_brain_state()
            
            return {
                "result": "success",
                "message": "Task resumed successfully",
                "data": self.brain_state.current_task.dict()
            }
        except Exception as e:
            logger.error(f"Error resuming task: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "result": "error",
                "message": f"Error: {str(e)}"
            } 