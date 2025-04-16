from fastapi import APIRouter, HTTPException, Response, status
from models.session import SessionCreate, SessionUpdate, SessionResponse, SessionListResponse
from services import session_service
from typing import Optional
from logging_config import setup_logger

# 로거 설정
logger = setup_logger("session_api")

router = APIRouter(
    prefix="/sessions",
    tags=["Session Management"],
    responses={404: {"description": "Session not found"}},
)

@router.post("/", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(session_create: SessionCreate = None):
    """새 대화 세션을 생성합니다."""
    logger.info("API 호출: 새 세션 생성")
    return session_service.create_session()

@router.get("/{session_id}", response_model=SessionResponse)
async def get_session(session_id: str):
    """세션 ID로 세션을 조회합니다."""
    logger.info(f"API 호출: 세션 조회 ({session_id})")
    session = session_service.get_session(session_id)
    
    if session is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    
    return session

@router.put("/{session_id}", response_model=SessionResponse)
async def update_session(session_id: str, session_update: SessionUpdate):
    """세션을 업데이트합니다."""
    logger.info(f"API 호출: 세션 업데이트 ({session_id})")
    
    updated_session = session_service.update_session(
        session_id=session_id,
        messages=session_update.messages,
        next_data=session_update.next
    )
    
    if updated_session is None:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    
    return updated_session

@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: str):
    """세션을 삭제합니다."""
    logger.info(f"API 호출: 세션 삭제 ({session_id})")
    
    result = session_service.delete_session(session_id)
    
    if not result:
        raise HTTPException(status_code=404, detail="세션을 찾을 수 없습니다.")
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.get("/", response_model=SessionListResponse)
async def list_sessions():
    """모든 세션 목록을 조회합니다."""
    logger.info("API 호출: 세션 목록 조회")
    return session_service.list_sessions() 