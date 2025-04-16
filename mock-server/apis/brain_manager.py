from fastapi import APIRouter, HTTPException
from services.brain_service import BrainService
from models.brain import (
    BrainResponse, BrainUpdateRequest, BrainAddRequest, BrainDeleteRequest,
    TaskContext
)
from typing import Dict, Any, Optional
from logging_config import setup_logger

# Brain Manager API용 로거 설정
logger = setup_logger("brain_manager_api")

# 라우터 및 서비스 초기화
router = APIRouter(prefix="/brain-manager", tags=["Brain Manager"])
service = BrainService()

@router.get("/")
async def get_brain_state() -> Dict[str, Any]:
    """브레인 상태 전체를 조회합니다."""
    logger.info("Getting full brain state")
    return service.get_brain_state()

@router.get("/path/{path:path}")
async def get_by_path(path: str) -> Dict[str, Any]:
    """경로로 브레인 상태의 특정 부분을 조회합니다.
    
    배열 항목에 접근할 때는 인덱스를 사용하지 않고 전체 배열을 반환합니다.
    
    예시:
    - /brain-manager/path/working_with_manager (Boolean 값 반환)
    - /brain-manager/path/current_task (현재 작업 객체 반환)
    - /brain-manager/path/todo_list (할일 목록 전체 배열 반환)
    - /brain-manager/path/paused_tasks (일시 중지된 작업 목록 전체 배열 반환)
    """
    logger.info(f"Getting brain state at path: {path}")
    return service.get_by_path(path)

@router.put("/update")
async def update_brain(request: BrainUpdateRequest) -> Dict[str, str]:
    """브레인 상태를 업데이트합니다.
    
    배열 항목은 인덱스를 사용하여 특정 항목을 업데이트할 수 있습니다:
    - todo_list[0] (할일 목록의 첫 번째 항목)
    - paused_tasks[1] (일시 중지된 작업 목록의 두 번째 항목)
    """
    logger.info(f"Updating brain state at path: {request.path}")
    return service.update_brain(request)

@router.post("/add")
async def add_item(request: BrainAddRequest) -> Dict[str, str]:
    """브레인 컬렉션에 항목을 추가합니다.
    
    유효한 컬렉션:
    - daily_activities
    - today_activities 
    - paused_tasks
    - todo_list
    """
    logger.info(f"Adding item to collection: {request.collection}")
    return service.add_item(request)

@router.delete("/delete")
async def delete_by_path(request: BrainDeleteRequest) -> Dict[str, str]:
    """경로로 브레인 상태의 특정 항목을 삭제합니다.
    
    배열 항목은 인덱스를 사용하여 특정 항목을 삭제할 수 있습니다:
    - todo_list[0] (할일 목록의 첫 번째 항목 삭제)
    - paused_tasks[1] (일시 중지된 작업 목록의 두 번째 항목 삭제)
    """
    logger.info(f"Deleting item at path: {request.path}")
    return service.delete_by_path(request)

@router.post("/current-task")
async def set_current_task(task_data: Dict[str, Any]) -> Dict[str, str]:
    """현재 작업을 설정합니다."""
    logger.info("Setting current task")
    return service.set_current_task(task_data)

@router.delete("/current-task")
async def reset_current_task() -> Dict[str, str]:
    """현재 작업을 초기화합니다."""
    logger.info("Resetting current task")
    return service.reset_current_task()

@router.post("/pause-task")
async def pause_current_task(request: Dict[str, str]) -> Dict[str, str]:
    """현재 작업을 일시 중지하고 보관합니다."""
    logger.info("Pausing current task")
    summary = request.get("summary", "작업 중단됨")
    return service.pause_current_task(summary)

@router.post("/resume-task/{task_index}")
async def resume_task(task_index: int) -> Dict[str, Any]:
    """일시 중지된 작업을 재개합니다.
    
    일시 중지된 작업 목록에서 지정된 인덱스의 작업을 재개합니다.
    작업 인덱스는 0부터 시작합니다.
    """
    logger.info(f"Resuming paused task at index: {task_index}")
    return service.resume_task(task_index) 