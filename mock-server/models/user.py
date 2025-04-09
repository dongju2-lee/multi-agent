from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime

class UserPersonalization(BaseModel):
    """사용자 개인화 정보 모델"""
    user_personalization_info: List[str] = []

class CalendarEvent(BaseModel):
    """캘린더 이벤트 모델"""
    time: str
    info: str

class CalendarDay(BaseModel):
    """하루의 일정 정보 모델"""
    events: List[CalendarEvent] = []

class CalendarInfo(BaseModel):
    """캘린더 정보 모델"""
    month: int = 4  # 기본값 4월
    info_of_day: Dict[str, List[CalendarEvent]] = {}

class Message(BaseModel):
    """메시지 모델"""
    message_name: str
    data: str  # 날짜 정보 (예: "2025-04-09:12:52:25")
    message_body: str

class UserMessageList(BaseModel):
    """사용자 메시지 목록 모델"""
    messages: List[Message] = []

class ResultResponse(BaseModel):
    """결과 응답 모델"""
    result: str
    message: Optional[str] = None

# 응답 모델들
class PersonalizationResponse(BaseModel):
    """개인화 정보 응답 모델"""
    result: str
    user_personalization_info: List[str]

class CalendarResponse(BaseModel):
    """캘린더 정보 응답 모델"""
    result: str
    calendar_info: Optional[CalendarInfo] = None

class MessageResponse(BaseModel):
    """메시지 정보 응답 모델"""
    result: str
    messages: Optional[List[Message]] = None

# 요청 모델들
class PersonalizationRequest(BaseModel):
    """개인화 정보 추가 요청 모델"""
    info: str

class CalendarEventRequest(BaseModel):
    """캘린더 이벤트 추가 요청 모델"""
    day: str  # 날짜 (예: "day1", "day2", ...)
    time: str  # 시간 (예: "14:00")
    info: str  # 일정 정보 (예: "점심약속")

class MessageRequest(BaseModel):
    """메시지 추가 요청 모델"""
    message_name: str
    data: str  # 날짜 정보
    message_body: str
