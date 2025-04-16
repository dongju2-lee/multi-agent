import json
import os
import time
from typing import Dict, Any, Optional, List, Protocol
from uuid import uuid4
import redis
from abc import ABC, abstractmethod
from langchain_core.messages import HumanMessage, BaseMessage, AIMessage, SystemMessage
from dotenv import load_dotenv
import traceback
from logging_config import setup_logger
import pathlib
import requests

# 로거 설정
logger = setup_logger("session_manager")

load_dotenv()

# 메시지 직렬화/역직렬화 함수
def serialize_message(message: BaseMessage) -> Dict[str, Any]:
    """메시지 객체를 직렬화합니다."""
    return {
        "type": message.__class__.__name__,
        "content": message.content,
        "name": getattr(message, "name", None),
        "additional_kwargs": message.additional_kwargs
    }

def deserialize_message(message_dict: Dict[str, Any]) -> BaseMessage:
    """직렬화된 메시지를 객체로 변환합니다."""
    message_type = message_dict["type"]
    content = message_dict["content"]
    name = message_dict.get("name")
    additional_kwargs = message_dict.get("additional_kwargs", {})
    
    if message_type == "HumanMessage":
        return HumanMessage(content=content, name=name, additional_kwargs=additional_kwargs)
    elif message_type == "AIMessage":
        return AIMessage(content=content, name=name, additional_kwargs=additional_kwargs)
    elif message_type == "SystemMessage":
        return SystemMessage(content=content, name=name, additional_kwargs=additional_kwargs)
    else:
        error_msg = f"알 수 없는 메시지 타입: {message_type}"
        logger.error(error_msg)
        raise ValueError(error_msg)

# 세션 관리자 인터페이스
class SessionManager(ABC):
    """대화 세션을 관리하는 추상 클래스."""
    
    @abstractmethod
    def create_session(self) -> str:
        """새 세션을 생성하고 세션 ID를 반환합니다."""
        pass
    
    @abstractmethod
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 ID로 세션 상태를 조회합니다."""
        pass
    
    @abstractmethod
    def update_session(self, session_id: str, state: Dict[str, Any]) -> None:
        """세션 상태를 업데이트합니다."""
        pass
    
    @abstractmethod
    def delete_session(self, session_id: str) -> bool:
        """세션을 삭제합니다."""
        pass
    
    @abstractmethod
    def list_sessions(self) -> Dict[str, Dict[str, Any]]:
        """모든 세션 목록을 반환합니다."""
        pass

# 메모리 기반 세션 관리자
class InMemorySessionManager(SessionManager):
    """메모리 기반 세션 관리자."""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        logger.info("메모리 기반 세션 관리자 초기화됨")
    
    def create_session(self) -> str:
        """새 세션을 생성하고 세션 ID를 반환합니다."""
        session_id = str(uuid4())
        self.sessions[session_id] = {
            "messages": [],
            "next": None
        }
        logger.info(f"새 세션 생성: {session_id}")
        return session_id
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 ID로 세션 상태를 조회합니다."""
        if session_id in self.sessions:
            logger.info(f"세션 조회: {session_id}")
            return self.sessions[session_id]
        logger.warning(f"존재하지 않는 세션 조회 시도: {session_id}")
        return None
    
    def update_session(self, session_id: str, state: Dict[str, Any]) -> None:
        """세션 상태를 업데이트합니다."""
        self.sessions[session_id] = state
        if "messages" in state:
            logger.info(f"세션 {session_id} 업데이트: 메시지 수 {len(state['messages'])}")
        else:
            logger.info(f"세션 {session_id} 업데이트")
    
    def delete_session(self, session_id: str) -> bool:
        """세션을 삭제합니다."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            logger.info(f"세션 삭제: {session_id}")
            return True
        logger.warning(f"존재하지 않는 세션 삭제 시도: {session_id}")
        return False
    
    def list_sessions(self) -> Dict[str, Dict[str, Any]]:
        """모든 세션 목록을 반환합니다."""
        session_info = {
            session_id: {
                "message_count": len(state["messages"])
            }
            for session_id, state in self.sessions.items()
        }
        logger.info(f"세션 목록 조회: {len(session_info)}개 세션")
        return session_info

# 파일 시스템 기반 세션 관리자
class FileSystemSessionManager(SessionManager):
    """파일 시스템 기반 세션 관리자."""
    
    def __init__(self, session_dir: Optional[str] = None, ttl: int = 86400):
        """
        파일 시스템 기반 세션 관리자를 초기화합니다.
        
        Args:
            session_dir: 세션 파일을 저장할 디렉토리. 없으면 기본 디렉토리를 사용합니다.
            ttl: 세션 유효 시간(초). 이 시간이 지난 세션은 조회 시 자동 삭제됩니다. 기본값은 24시간.
        """
        self.ttl = ttl
        self.session_dir = session_dir or os.path.join(os.path.dirname(os.path.abspath(__file__)), "session_store")
        
        # 세션 디렉토리가 없으면 생성
        pathlib.Path(self.session_dir).mkdir(exist_ok=True)
        logger.info(f"파일 시스템 기반 세션 관리자 초기화됨 (디렉토리: {self.session_dir}, TTL: {self.ttl}초)")
    
    def _get_file_path(self, session_id: str) -> str:
        """세션 ID에 해당하는 파일 경로를 반환합니다."""
        return os.path.join(self.session_dir, f"{session_id}.json")
    
    def create_session(self) -> str:
        """새 세션을 생성하고 세션 ID를 반환합니다."""
        session_id = str(uuid4())
        state = {
            "messages": [],
            "next": None,
            "created_at": time.time(),
            "updated_at": time.time()
        }
        
        # 메시지 직렬화
        serialized_state = {
            "messages": [],
            "next": None,
            "created_at": state["created_at"],
            "updated_at": state["updated_at"]
        }
        
        # 파일에 저장
        try:
            file_path = self._get_file_path(session_id)
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(serialized_state, f, ensure_ascii=False, indent=2)
            logger.info(f"파일 시스템에 새 세션 생성: {session_id} (위치: {file_path})")
            return session_id
        except Exception as e:
            error_msg = f"파일 시스템 세션 생성 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            raise
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 ID로 세션 상태를 조회합니다."""
        file_path = self._get_file_path(session_id)
        
        try:
            if not os.path.exists(file_path):
                logger.warning(f"파일 시스템에서 존재하지 않는 세션 조회 시도: {session_id}")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                serialized_state = json.load(f)
            
            # TTL 체크
            current_time = time.time()
            if current_time - serialized_state.get("updated_at", 0) > self.ttl:
                logger.info(f"세션 {session_id} TTL 만료로 삭제됨")
                self.delete_session(session_id)
                return None
            
            # 메시지 객체로 변환
            state = {
                "messages": [
                    deserialize_message(msg) for msg in serialized_state.get("messages", [])
                ],
                "next": serialized_state.get("next"),
                "created_at": serialized_state.get("created_at"),
                "updated_at": serialized_state.get("updated_at")
            }
            
            logger.info(f"파일 시스템에서 세션 조회: {session_id} (메시지 수: {len(state['messages'])})")
            return state
        except Exception as e:
            error_msg = f"파일 시스템 세션 조회 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return None
    
    def update_session(self, session_id: str, state: Dict[str, Any]) -> None:
        """세션 상태를 업데이트합니다."""
        try:
            # 기존 상태에서 타임스탬프 정보 가져오기
            created_at = time.time()
            file_path = self._get_file_path(session_id)
            
            if os.path.exists(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    old_state = json.load(f)
                    created_at = old_state.get("created_at", created_at)
            
            # 메시지 직렬화
            serialized_state = {
                "messages": [
                    serialize_message(msg) for msg in state.get("messages", [])
                ],
                "next": state.get("next"),
                "created_at": created_at,
                "updated_at": time.time()
            }
            
            # 파일에 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(serialized_state, f, ensure_ascii=False, indent=2)
            
            if "messages" in state:
                logger.info(f"파일 시스템 세션 {session_id} 업데이트: 메시지 수 {len(state['messages'])}")
            else:
                logger.info(f"파일 시스템 세션 {session_id} 업데이트")
        except Exception as e:
            error_msg = f"파일 시스템 세션 업데이트 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
    
    def delete_session(self, session_id: str) -> bool:
        """세션을 삭제합니다."""
        file_path = self._get_file_path(session_id)
        
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"파일 시스템 세션 삭제: {session_id}")
                return True
            else:
                logger.warning(f"파일 시스템에서 존재하지 않는 세션 삭제 시도: {session_id}")
                return False
        except Exception as e:
            error_msg = f"파일 시스템 세션 삭제 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return False
    
    def list_sessions(self) -> Dict[str, Dict[str, Any]]:
        """모든 세션 목록을 반환합니다."""
        result = {}
        current_time = time.time()
        
        try:
            for file_name in os.listdir(self.session_dir):
                if not file_name.endswith('.json'):
                    continue
                
                session_id = file_name[:-5]  # .json 제거
                file_path = self._get_file_path(session_id)
                
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # TTL 체크
                    updated_at = data.get("updated_at", 0)
                    if current_time - updated_at > self.ttl:
                        # TTL이 지난 세션은 삭제
                        logger.info(f"세션 {session_id} TTL 만료로 삭제됨")
                        os.remove(file_path)
                        continue
                    
                    result[session_id] = {
                        "message_count": len(data.get("messages", [])),
                        "created_at": data.get("created_at"),
                        "updated_at": updated_at,
                        "ttl_remaining": int(self.ttl - (current_time - updated_at))
                    }
                except Exception as e:
                    logger.error(f"세션 파일 {file_name} 읽기 실패: {str(e)}")
            
            logger.info(f"파일 시스템 세션 목록 조회: {len(result)}개 세션")
            return result
        except Exception as e:
            error_msg = f"파일 시스템 세션 목록 조회 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {}

# Redis 기반 세션 관리자
class RedisSessionManager(SessionManager):
    """Redis 기반 세션 관리자."""
    
    def __init__(self, redis_url: Optional[str] = None, ttl: int = 86400):
        """
        Redis 연결을 초기화합니다.
        
        Args:
            redis_url: Redis 연결 URL. 없으면 환경 변수에서 가져옵니다.
            ttl: 세션 만료 시간(초). 기본값은 24시간.
        """
        self.redis_url = redis_url or os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self.ttl = ttl
        self.prefix = "smarthome:session:"
        
        try:
            logger.info(f"Redis 연결 시도: {self.redis_url}")
            self.redis_client = redis.from_url(self.redis_url)
            logger.info("Redis 연결 성공")
        except Exception as e:
            error_msg = f"Redis 연결 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            raise
    
    def _get_key(self, session_id: str) -> str:
        """세션 ID로부터 Redis 키를 생성합니다."""
        return f"{self.prefix}{session_id}"
    
    def create_session(self) -> str:
        """새 세션을 생성하고 세션 ID를 반환합니다."""
        session_id = str(uuid4())
        state = {
            "messages": [],
            "next": None
        }
        
        # 메시지 직렬화
        serialized_state = {
            "messages": [],
            "next": None
        }
        
        # Redis에 저장
        try:
            self.redis_client.set(
                self._get_key(session_id),
                json.dumps(serialized_state),
                ex=self.ttl
            )
            logger.info(f"Redis에 새 세션 생성: {session_id} (TTL: {self.ttl}초)")
            return session_id
        except Exception as e:
            error_msg = f"Redis 세션 생성 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            raise
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 ID로 세션 상태를 조회합니다."""
        try:
            data = self.redis_client.get(self._get_key(session_id))
            if not data:
                logger.warning(f"Redis에서 존재하지 않는 세션 조회 시도: {session_id}")
                return None
            
            # 역직렬화
            serialized_state = json.loads(data)
            
            # 메시지 객체로 변환
            state = {
                "messages": [
                    deserialize_message(msg) for msg in serialized_state.get("messages", [])
                ],
                "next": serialized_state.get("next")
            }
            
            # TTL 갱신
            self.redis_client.expire(self._get_key(session_id), self.ttl)
            logger.info(f"Redis에서 세션 조회: {session_id} (메시지 수: {len(state['messages'])})")
            
            return state
        except Exception as e:
            error_msg = f"Redis 세션 조회 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return None
    
    def update_session(self, session_id: str, state: Dict[str, Any]) -> None:
        """세션 상태를 업데이트합니다."""
        try:
            # 메시지 직렬화
            serialized_state = {
                "messages": [
                    serialize_message(msg) for msg in state.get("messages", [])
                ],
                "next": state.get("next")
            }
            
            # Redis에 저장
            self.redis_client.set(
                self._get_key(session_id),
                json.dumps(serialized_state),
                ex=self.ttl
            )
            
            if "messages" in state:
                logger.info(f"Redis 세션 {session_id} 업데이트: 메시지 수 {len(state['messages'])}")
            else:
                logger.info(f"Redis 세션 {session_id} 업데이트")
        except Exception as e:
            error_msg = f"Redis 세션 업데이트 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
    
    def delete_session(self, session_id: str) -> bool:
        """세션을 삭제합니다."""
        try:
            result = bool(self.redis_client.delete(self._get_key(session_id)))
            if result:
                logger.info(f"Redis 세션 삭제: {session_id}")
            else:
                logger.warning(f"Redis에서 존재하지 않는 세션 삭제 시도: {session_id}")
            return result
        except Exception as e:
            error_msg = f"Redis 세션 삭제 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return False
    
    def list_sessions(self) -> Dict[str, Dict[str, Any]]:
        """모든 세션 목록을 반환합니다."""
        try:
            keys = self.redis_client.keys(f"{self.prefix}*")
            result = {}
            
            for key in keys:
                session_id = key.decode("utf-8").replace(self.prefix, "")
                data = self.redis_client.get(key)
                if data:
                    serialized_state = json.loads(data)
                    result[session_id] = {
                        "message_count": len(serialized_state.get("messages", [])),
                        "ttl": self.redis_client.ttl(key)
                    }
            
            logger.info(f"Redis 세션 목록 조회: {len(result)}개 세션")
            return result
        except Exception as e:
            error_msg = f"Redis 세션 목록 조회 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {}

# API 기반 세션 관리자
class APISessionManager(SessionManager):
    """API 기반 세션 관리자."""
    
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None):
        """
        API 기반 세션 관리자를 초기화합니다.
        
        Args:
            base_url: API 서버 기본 URL. 없으면 환경 변수에서 가져옵니다.
            api_key: API 인증 키. 없으면 환경 변수에서 가져옵니다.
        """
        self.base_url = base_url or os.environ.get("SESSION_API_URL", "http://localhost:8000")
        self.api_key = api_key or os.environ.get("SESSION_API_KEY", "")
        self.session_url = f"{self.base_url}/sessions"
        
        # HTTP 세션 초기화
        self.http_session = requests.Session()
        
        # API 키가 있으면 헤더에 추가
        if self.api_key:
            self.http_session.headers.update({"Authorization": f"Bearer {self.api_key}"})
        
        logger.info(f"API 기반 세션 관리자 초기화됨 (API 서버: {self.base_url})")
    
    def create_session(self) -> str:
        """새 세션을 생성하고 세션 ID를 반환합니다."""
        try:
            response = self.http_session.post(self.session_url)
            response.raise_for_status()  # HTTP 오류 체크
            
            data = response.json()
            session_id = data.get("session_id")
            
            logger.info(f"API 서버에 새 세션 생성: {session_id}")
            return session_id
        except Exception as e:
            error_msg = f"API 세션 생성 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            raise
    
    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """세션 ID로 세션 상태를 조회합니다."""
        try:
            response = self.http_session.get(f"{self.session_url}/{session_id}")
            
            if response.status_code == 404:
                logger.warning(f"API 서버에서 존재하지 않는 세션 조회 시도: {session_id}")
                return None
            
            response.raise_for_status()  # 기타 HTTP 오류 체크
            
            session_data = response.json()
            
            # 메시지 객체로 변환
            messages = []
            for msg_data in session_data.get("messages", []):
                messages.append(deserialize_message({
                    "type": msg_data.get("type"),
                    "content": msg_data.get("content", ""),
                    "name": msg_data.get("name"),
                    "additional_kwargs": msg_data.get("additional_kwargs", {})
                }))
            
            # 응답 데이터 구성
            state = {
                "messages": messages,
                "next": session_data.get("next"),
                "created_at": session_data.get("created_at"),
                "updated_at": session_data.get("updated_at")
            }
            
            logger.info(f"API 서버에서 세션 조회: {session_id} (메시지 수: {len(messages)})")
            return state
            
        except Exception as e:
            error_msg = f"API 세션 조회 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return None
    
    def update_session(self, session_id: str, state: Dict[str, Any]) -> None:
        """세션 상태를 업데이트합니다."""
        try:
            # 메시지 직렬화
            messages_data = []
            for msg in state.get("messages", []):
                messages_data.append(serialize_message(msg))
            
            # 요청 데이터 구성
            request_data = {
                "messages": messages_data,
                "next": state.get("next")
            }
            
            # API 호출
            response = self.http_session.put(
                f"{self.session_url}/{session_id}",
                json=request_data
            )
            
            response.raise_for_status()  # HTTP 오류 체크
            
            if "messages" in state:
                logger.info(f"API 세션 {session_id} 업데이트: 메시지 수 {len(state['messages'])}")
            else:
                logger.info(f"API 세션 {session_id} 업데이트")
                
        except Exception as e:
            error_msg = f"API 세션 업데이트 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
    
    def delete_session(self, session_id: str) -> bool:
        """세션을 삭제합니다."""
        try:
            response = self.http_session.delete(f"{self.session_url}/{session_id}")
            
            if response.status_code == 404:
                logger.warning(f"API 서버에서 존재하지 않는 세션 삭제 시도: {session_id}")
                return False
            
            response.raise_for_status()  # HTTP 오류 체크
            logger.info(f"API 세션 삭제: {session_id}")
            return True
            
        except Exception as e:
            error_msg = f"API 세션 삭제 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return False
    
    def list_sessions(self) -> Dict[str, Dict[str, Any]]:
        """모든 세션 목록을 반환합니다."""
        try:
            response = self.http_session.get(self.session_url)
            response.raise_for_status()  # HTTP 오류 체크
            
            data = response.json()
            sessions = data.get("sessions", {})
            
            logger.info(f"API 세션 목록 조회: {len(sessions)}개 세션")
            return sessions
            
        except Exception as e:
            error_msg = f"API 세션 목록 조회 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {}

# 세션 관리자 팩토리
def create_session_manager() -> SessionManager:
    """
    설정에 따라 적절한 세션 관리자를 생성합니다.
    REDIS_URL 환경 변수가 설정되어 있으면 Redis 기반 관리자를,
    USE_FILE_SESSION 환경 변수가 설정되어 있으면 파일 시스템 기반 관리자를,
    그렇지 않으면 메모리 기반 관리자를 반환합니다.
    """
    redis_url = os.environ.get("REDIS_URL")
    use_file_session = os.environ.get("USE_FILE_SESSION", "true").lower() in ("true", "1", "yes")
    
    if redis_url:
        logger.info(f"Redis 기반 세션 관리자 사용: {redis_url}")
        try:
            return RedisSessionManager(redis_url)
        except Exception as e:
            logger.error(f"Redis 세션 관리자 생성 실패, 파일 시스템 세션 관리자로 대체: {str(e)}")
            if use_file_session:
                return FileSystemSessionManager()
            return InMemorySessionManager()
    
    if use_file_session:
        session_dir = os.environ.get("SESSION_STORE_DIR")
        logger.info(f"파일 시스템 기반 세션 관리자 사용 (디렉토리: {session_dir or '기본 디렉토리'})")
        return FileSystemSessionManager(session_dir)
    
    logger.info("메모리 기반 세션 관리자 사용")
    return InMemorySessionManager()

def get_session_manager(manager_type: str = "in_memory") -> SessionManager:
    """
    지정된 유형의 세션 매니저 객체를 반환합니다.
    
    Args:
        manager_type: 세션 매니저 유형 ('in_memory', 'file_system', 'redis', 'api')
    
    Returns:
        적절한 유형의 SessionManager 객체
    """
    manager_type = manager_type.lower()
    
    logger.info(f"세션 매니저 가져오기: 유형={manager_type}")
    
    # 세션 매니저 유형에 따라 인스턴스 생성
    if manager_type == "in_memory":
        logger.info("메모리 기반 세션 매니저를 생성합니다.")
        return InMemorySessionManager()
    elif manager_type == "file_system":
        logger.info("파일 시스템 기반 세션 매니저를 생성합니다.")
        session_dir = os.environ.get("SESSION_STORE_DIR")
        session_manager = FileSystemSessionManager(session_dir)
        # 세션 목록 테스트
        try:
            sessions = session_manager.list_sessions()
            logger.info(f"파일 시스템 세션 매니저 초기화 완료. 현재 {len(sessions)}개의 세션이 있습니다.")
            for session_id, info in sessions.items():
                logger.info(f"세션 ID: {session_id}, 메시지 수: {info.get('message_count', 0)}")
        except Exception as e:
            logger.error(f"세션 목록 조회 테스트 중 오류 발생: {str(e)}")
        return session_manager
    elif manager_type == "redis":
        logger.info("Redis 기반 세션 매니저를 생성합니다.")
        return RedisSessionManager()
    elif manager_type == "api":
        logger.info("API 기반 세션 매니저를 생성합니다.")
        return APISessionManager()
    else:
        # 기본값은 in-memory
        logger.warning(f"알 수 없는 세션 매니저 유형: {manager_type}, in-memory 사용")
        return InMemorySessionManager() 