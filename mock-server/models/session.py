from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from uuid import UUID


class MessageType(str, Enum):
    """메시지 타입 열거형"""
    HUMAN = "HumanMessage"
    AI = "AIMessage"
    SYSTEM = "SystemMessage"


class Message(BaseModel):
    """메시지 모델"""
    type: MessageType
    content: str
    name: Optional[str] = None
    additional_kwargs: Dict[str, Any] = {}


class Session(BaseModel):
    """세션 모델"""
    session_id: str
    messages: List[Message] = []
    next: Optional[Dict[str, Any]] = None
    created_at: float
    updated_at: float


class SessionCreate(BaseModel):
    """세션 생성 요청 모델"""
    pass  # 비어있는 요청 본문으로도 세션 생성 가능


class SessionUpdate(BaseModel):
    """세션 업데이트 요청 모델"""
    messages: List[Message]
    next: Optional[Dict[str, Any]] = None


class SessionResponse(BaseModel):
    """세션 응답 모델"""
    session_id: str
    messages: List[Message]
    next: Optional[Dict[str, Any]] = None
    created_at: float
    updated_at: float


class SessionListResponse(BaseModel):
    """세션 목록 응답 모델"""
    sessions: Dict[str, Dict[str, Any]] 