from models.session import Message, Session, SessionResponse, SessionListResponse, MessageType
from typing import Dict, List, Optional, Any
import time
import json
import os
import uuid
from logging_config import setup_logger

# 로거 설정
logger = setup_logger("session_service")

# 세션 스토리지 디렉토리
SESSION_STORE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "session_store")
os.makedirs(SESSION_STORE_DIR, exist_ok=True)

# 인메모리 세션 스토리지 (개발 및 테스트용)
_sessions: Dict[str, Dict[str, Any]] = {}

def _get_file_path(session_id: str) -> str:
    """세션 ID에 해당하는 파일 경로를 반환합니다."""
    return os.path.join(SESSION_STORE_DIR, f"{session_id}.json")

def create_session() -> SessionResponse:
    """새로운 세션을 생성합니다."""
    logger.info("새 세션 생성 요청")
    
    session_id = str(uuid.uuid4())
    now = time.time()
    
    session_data = {
        "session_id": session_id,
        "messages": [],
        "next": None,
        "created_at": now,
        "updated_at": now
    }
    
    # 파일에 저장
    try:
        file_path = _get_file_path(session_id)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
        logger.info(f"새 세션 생성 완료: {session_id} (파일: {file_path})")
    except Exception as e:
        logger.error(f"파일 저장 중 오류 발생: {str(e)}")
    
    # 인메모리 저장 (옵션)
    _sessions[session_id] = session_data
    
    return SessionResponse(**session_data)

def get_session(session_id: str) -> Optional[SessionResponse]:
    """세션 ID로 세션을 조회합니다."""
    logger.info(f"세션 조회 요청: {session_id}")
    
    # 파일에서 읽기
    file_path = _get_file_path(session_id)
    
    if not os.path.exists(file_path):
        logger.warning(f"존재하지 않는 세션: {session_id}")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
        
        # 메시지 객체로 변환
        messages = []
        for msg_data in session_data.get("messages", []):
            msg_type = msg_data.get("type", "HumanMessage")
            messages.append(Message(
                type=msg_type,
                content=msg_data.get("content", ""),
                name=msg_data.get("name"),
                additional_kwargs=msg_data.get("additional_kwargs", {})
            ))
        
        session_data["messages"] = messages
        
        # 인메모리 캐시 업데이트
        _sessions[session_id] = session_data
        
        logger.info(f"세션 조회 성공: {session_id} (메시지 수: {len(messages)})")
        return SessionResponse(**session_data)
    
    except Exception as e:
        logger.error(f"세션 조회 중 오류: {str(e)}")
        return None

def update_session(session_id: str, messages: List[Message], next_data: Optional[Dict[str, Any]] = None) -> Optional[SessionResponse]:
    """세션을 업데이트합니다."""
    logger.info(f"세션 업데이트 요청: {session_id}")
    
    # 기존 세션 확인
    file_path = _get_file_path(session_id)
    if not os.path.exists(file_path):
        logger.warning(f"존재하지 않는 세션 업데이트 시도: {session_id}")
        return None
    
    # 기존 세션 데이터 가져오기
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            session_data = json.load(f)
    except Exception as e:
        logger.error(f"세션 데이터 읽기 오류: {str(e)}")
        return None
    
    # 메시지 직렬화
    messages_data = []
    for msg in messages:
        messages_data.append({
            "type": msg.type,
            "content": msg.content,
            "name": msg.name,
            "additional_kwargs": msg.additional_kwargs
        })
    
    # 데이터 업데이트
    session_data["messages"] = messages_data
    session_data["next"] = next_data
    session_data["updated_at"] = time.time()
    
    # 파일 저장
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
        
        # 인메모리 캐시 업데이트
        _sessions[session_id] = session_data
        
        logger.info(f"세션 업데이트 완료: {session_id} (메시지 수: {len(messages)})")
        
        # 응답 준비
        session_data["messages"] = messages  # 객체 버전으로 다시 교체
        return SessionResponse(**session_data)
    
    except Exception as e:
        logger.error(f"세션 저장 중 오류: {str(e)}")
        return None

def delete_session(session_id: str) -> bool:
    """세션을 삭제합니다."""
    logger.info(f"세션 삭제 요청: {session_id}")
    
    file_path = _get_file_path(session_id)
    
    if not os.path.exists(file_path):
        logger.warning(f"존재하지 않는 세션 삭제 시도: {session_id}")
        return False
    
    try:
        # 파일 삭제
        os.remove(file_path)
        
        # 인메모리 캐시에서 제거
        if session_id in _sessions:
            del _sessions[session_id]
        
        logger.info(f"세션 삭제 완료: {session_id}")
        return True
    
    except Exception as e:
        logger.error(f"세션 삭제 중 오류: {str(e)}")
        return False

def list_sessions() -> SessionListResponse:
    """모든 세션 목록을 조회합니다."""
    logger.info("세션 목록 조회 요청")
    
    sessions = {}
    
    # 파일 목록 조회
    try:
        for filename in os.listdir(SESSION_STORE_DIR):
            if filename.endswith('.json'):
                session_id = filename[:-5]  # .json 제거
                file_path = os.path.join(SESSION_STORE_DIR, filename)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                # 필요한 메타데이터만 포함
                sessions[session_id] = {
                    "message_count": len(session_data.get("messages", [])),
                    "created_at": session_data.get("created_at"),
                    "updated_at": session_data.get("updated_at")
                }
        
        logger.info(f"세션 목록 조회 완료: {len(sessions)}개 세션")
        return SessionListResponse(sessions=sessions)
    
    except Exception as e:
        logger.error(f"세션 목록 조회 중 오류: {str(e)}")
        return SessionListResponse(sessions={}) 