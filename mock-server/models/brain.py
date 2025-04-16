from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class Activity(BaseModel):
    """활동 정보 모델"""
    time: str
    session_id: str
    summary: str


class TaskContext(BaseModel):
    """작업 컨텍스트 모델"""
    agent_name: str = ""
    task_name: str = ""
    details: str = ""
    session_id: str = ""
    start_time: str
    last_updated: Optional[str] = None
    pause_time: Optional[str] = None


class PausedTask(BaseModel):
    """일시 중지된 작업 모델"""
    time: str
    session_id: str
    summary: str
    task_context: TaskContext


class TodoItem(BaseModel):
    """할 일 항목 모델"""
    request_time: str
    session_id: str
    summary: str


class BrainState(BaseModel):
    """브레인 상태 전체 모델"""
    daily_activities: List[Activity] = []
    today_activities: List[Activity] = []
    working_with_manager: bool = False
    current_task: Optional[TaskContext] = None
    paused_tasks: List[PausedTask] = []
    todo_list: List[TodoItem] = []


class BrainUpdateRequest(BaseModel):
    """브레인 업데이트 요청 모델"""
    path: str  # 업데이트할 경로 (예: "working_with_manager", "current_task", "todo_list[0]")
    value: Any  # 새 값


class BrainAddRequest(BaseModel):
    """브레인에 항목 추가 요청 모델"""
    collection: str  # 추가할 컬렉션 (예: "daily_activities", "paused_tasks", "todo_list")
    item: Dict[str, Any]  # 추가할 항목


class BrainDeleteRequest(BaseModel):
    """브레인에서 항목 삭제 요청 모델"""
    path: str  # 삭제할 경로 (예: "todo_list[0]", "paused_tasks[1]")


class BrainResponse(BaseModel):
    """브레인 응답 모델"""
    result: str
    message: Optional[str] = None
    data: Optional[Dict[str, Any]] = None 