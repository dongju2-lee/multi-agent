from fastapi import APIRouter, HTTPException
from services.user_service import UserService
from models.user import (
    PersonalizationRequest, CalendarEventRequest,
    MessageRequest, ResultResponse
)
from typing import Dict, List, Any
from logging_config import setup_logger

# User API용 로거 설정
logger = setup_logger("user_api")

# 라우터 및 서비스 초기화
router = APIRouter(prefix="/user", tags=["user"])
service = UserService()

# 개인화 정보 관련 엔드포인트
@router.get("/personalization")
async def get_personalization() -> Dict[str, Any]:
    """사용자 개인화 정보를 조회합니다."""
    logger.info("Getting user personalization info")
    result = service.get_personalization()
    logger.info(f"User personalization info retrieved: {len(result['user_personalization_info'])} items")
    return result

@router.post("/personalization")
async def add_personalization(request: PersonalizationRequest) -> ResultResponse:
    """사용자 개인화 정보를 추가합니다."""
    logger.info(f"Adding user personalization info: {request.info}")
    result = service.add_personalization(request.info)
    logger.info("User personalization info added successfully")
    return ResultResponse(**result)

# 캘린더 관련 엔드포인트
@router.get("/calendar")
async def get_calendar() -> Dict[str, Any]:
    """사용자 캘린더 정보를 조회합니다."""
    logger.info("Getting user calendar info")
    result = service.get_calendar()
    calendar_info = result.get("calendar_info", {})
    days_count = len(calendar_info.get("info_of_day", {}))
    logger.info(f"User calendar info retrieved: {days_count} days with events")
    return result

@router.post("/calendar")
async def add_calendar_event(request: CalendarEventRequest) -> ResultResponse:
    """사용자 캘린더에 이벤트를 추가합니다."""
    logger.info(f"Adding calendar event: day={request.day}, time={request.time}, info={request.info}")
    result = service.add_calendar_event(request.day, request.time, request.info)
    logger.info("Calendar event added successfully")
    return ResultResponse(**result)

# 메시지 관련 엔드포인트
@router.get("/message")
async def get_messages() -> Dict[str, Any]:
    """사용자 메시지 목록을 조회합니다."""
    logger.info("Getting user messages")
    result = service.get_messages()
    messages_count = len(result.get("messages", []))
    logger.info(f"User messages retrieved: {messages_count} messages")
    return result

@router.post("/message")
async def add_message(request: MessageRequest) -> ResultResponse:
    """사용자에게 메시지를 추가합니다."""
    logger.info(f"Adding message: {request.message_name}")
    result = service.add_message(
        request.message_name,
        request.data,
        request.message_body
    )
    logger.info("Message added successfully")
    return ResultResponse(**result)
