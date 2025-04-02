import os
import streamlit as st
import asyncio
import nest_asyncio
from typing import Optional, Dict, Any, List
import uuid
import json
import sys
import time
import datetime

# 현재 디렉토리를 시스템 경로에 추가하여 상대 임포트가 가능하도록 함
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# nest_asyncio 적용: 이미 실행 중인 이벤트 루프 내에서 중첩 호출 허용
nest_asyncio.apply()

# 전역 이벤트 루프 생성 및 재사용 (한번 생성한 후 계속 사용)
if "event_loop" not in st.session_state:
    loop = asyncio.new_event_loop()
    st.session_state.event_loop = loop
    asyncio.set_event_loop(loop)

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.messages.ai import AIMessageChunk
from langchain_core.runnables import RunnableConfig
from dotenv import load_dotenv
from logging_config import setup_logger

# 스마트홈 에이전트 및 그래프 가져오기
from graphs.smarthome_graph import get_smarthome_graph, get_mermaid_graph
from session_manager import FileSystemSessionManager

# MCP 클라이언트 및 도구 가져오기 (사이드바 MCP 정보 표시용)
from agents.robot_cleaner_agent import init_mcp_client, get_tools_with_details

# 환경 변수 로드
load_dotenv(override=True)

# 로거 설정
logger = setup_logger("streamlit_app")

async def refresh_mcp_info():
    """MCP 클라이언트 정보를 새로고침합니다."""
    try:
        logger.info("MCP 정보 새로고침 시작")
        
        # MCP 클라이언트 초기화 (강제로 초기화)
        from agents.robot_cleaner_agent import _mcp_client
        
        # 클라이언트가 이미 초기화되어 있다면 재사용
        if _mcp_client is not None:
            client = _mcp_client
            logger.info("기존 MCP 클라이언트 사용")
        else:
            # 새로 초기화
            client = await init_mcp_client()
            logger.info("새 MCP 클라이언트 초기화 완료")
        
        # MCP 도구 가져오기
        tools = await get_tools_with_details()
        logger.info(f"MCP 도구 {len(tools)}개 로드 완료")
        
        # 결과 반환
        return {
            "status": "initialized",
            "servers": client.servers if hasattr(client, "servers") else {},
            "tools_count": len(tools),
            "tools": tools
        }
    except Exception as e:
        logger.error(f"MCP 정보 새로고침 중 오류 발생: {str(e)}")
        return {"status": "error", "error": str(e)}

# 세션 관리자 초기화
if "session_manager" not in st.session_state:
    session_store_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "session_store")
    st.session_state.session_manager = FileSystemSessionManager(session_dir=session_store_path)
    logger.info(f"세션 관리자 초기화 완료 (저장 위치: {session_store_path})")

# 세션 상태에 초기화 진행 플래그 추가 (이미 완료했지만 아직 새로고침 안된 상태 구분)
if "initialization_completed" not in st.session_state:
    st.session_state.initialization_completed = False

# 페이지 설정: 제목, 아이콘, 레이아웃 구성
st.set_page_config(page_title="스마트홈 관리 시스템", page_icon="🏠", layout="wide")

# 페이지 제목 및 설명
st.title("🏠 스마트홈 관리 시스템")
st.markdown("✨ 스마트홈 시스템을 관리할 수 있는 멀티에이전트 시스템입니다. 원하는 질문이나 명령을 입력해보세요!")

# 세션 상태 초기화
if "session_initialized" not in st.session_state:
    st.session_state.session_initialized = False  # 세션 초기화 상태 플래그
    st.session_state.graph = None  # 그래프 객체 저장 공간
    st.session_state.history = []  # 대화 기록 저장 리스트
    st.session_state.thread_id = str(uuid.uuid4())  # 세션 고유 ID

# 탭 관리를 위한 세션 상태 초기화
if "active_tabs" not in st.session_state:
    st.session_state.active_tabs = []  # 열려있는 세션 탭 목록
    st.session_state.active_session_id = None  # 현재 활성화된 세션 ID

# 세션 관리 함수들
def create_new_session():
    """새로운 세션을 생성합니다."""
    # 현재 세션 저장
    if st.session_state.session_initialized and st.session_state.history:
        save_current_session()
    
    # 새 세션 생성
    session_id = st.session_state.session_manager.create_session()
    st.session_state.thread_id = session_id
    st.session_state.history = []
    
    # 새 세션을 메인 탭으로 설정
    st.session_state.active_session_id = session_id
    
    # 탭 목록 업데이트
    if session_id not in st.session_state.active_tabs:
        st.session_state.active_tabs.append(session_id)
    
    logger.info(f"새 세션 생성됨: {session_id}")
    
    # 세션 상태 UI 업데이트
    st.success("✅ 새 세션이 생성되었습니다!")
    st.rerun()

def dict_to_langchain_message(message_dict):
    """
    딕셔너리 형식의 메시지를 LangChain 메시지 객체로 변환합니다.
    
    Args:
        message_dict: 딕셔너리 형식의 메시지
    
    Returns:
        LangChain 메시지 객체
    """
    role = message_dict.get("role", "")
    content = message_dict.get("content", "")
    name = message_dict.get("name")
    
    if role == "user":
        return HumanMessage(content=content, name=name)
    elif role == "assistant":
        return AIMessage(content=content, name=name)
    elif role == "agent":
        # agent 역할은 AIMessage로 변환하고 이름 보존
        return AIMessage(content=content, name=name)
    else:
        # 기본적으로 HumanMessage 반환
        return HumanMessage(content=content)

def save_current_session():
    """현재 세션을 저장합니다."""
    if not st.session_state.session_initialized:
        logger.warning("초기화되지 않은 세션을 저장하려고 시도함")
        return False
    
    try:
        # 딕셔너리 메시지를 LangChain 메시지 객체로 변환
        langchain_messages = []
        for msg in st.session_state.history:
            try:
                langchain_messages.append(dict_to_langchain_message(msg))
            except Exception as e:
                logger.warning(f"메시지 변환 중 오류 발생: {str(e)}")
        
        # 세션 상태 생성
        session_data = {
            "messages": langchain_messages,
            "next": None,
        }
        
        # 세션 저장
        st.session_state.session_manager.update_session(st.session_state.thread_id, session_data)
        logger.info(f"세션 {st.session_state.thread_id} 저장됨 (메시지 수: {len(st.session_state.history)})")
        return True
    except Exception as e:
        import traceback
        logger.error(f"세션 저장 실패: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def load_session(session_id: str):
    """지정된 세션을 불러옵니다."""
    # 세션 데이터 가져오기
    session_data = st.session_state.session_manager.get_session(session_id)
    if not session_data:
        logger.warning(f"존재하지 않는 세션을 불러오려고 시도함: {session_id}")
        st.error("❌ 세션을 불러올 수 없습니다!")
        return False
    
    # 현재 세션 저장
    if st.session_state.session_initialized and st.session_state.history:
        save_current_session()
    
    # 탭 목록에 추가
    if session_id not in st.session_state.active_tabs:
        st.session_state.active_tabs.append(session_id)
    
    # 현재 활성 세션으로 설정
    st.session_state.active_session_id = session_id
    
    logger.info(f"세션 {session_id} 불러오기 완료")
    st.success(f"✅ 세션 '{session_id[:8]}...'이(가) 열렸습니다!")
    st.rerun()

def close_tab(session_id: str):
    """열려있는 세션 탭을 닫습니다."""
    if session_id in st.session_state.active_tabs:
        # 탭 목록에서 제거
        st.session_state.active_tabs.remove(session_id)
        
        # 현재 활성화된 세션이 닫히는 경우, 다른 세션으로 전환
        if st.session_state.active_session_id == session_id:
            if st.session_state.active_tabs:
                # 다른 열린 탭이 있으면 첫 번째로 전환
                st.session_state.active_session_id = st.session_state.active_tabs[0]
            else:
                # 열린 탭이 없으면 현재 세션 유지
                st.session_state.active_session_id = st.session_state.thread_id
        
        logger.info(f"세션 탭 닫힘: {session_id}")
        st.rerun()

def switch_tab(session_id: str):
    """다른 세션 탭으로 전환합니다."""
    # 현재 세션 저장
    if st.session_state.session_initialized and st.session_state.history:
        save_current_session()
    
    # 활성 세션 전환
    st.session_state.active_session_id = session_id
    
    logger.info(f"세션 탭 전환: {session_id}")
    st.rerun()

def get_session_history(session_id: str) -> List[Dict]:
    """특정 세션의 대화 기록을 가져옵니다."""
    # 현재 세션인 경우 현재 기록 반환
    if session_id == st.session_state.thread_id:
        return st.session_state.history
    
    # 저장된 세션 데이터 가져오기
    session_data = st.session_state.session_manager.get_session(session_id)
    if not session_data:
        return []
    
    # LangChain 메시지 객체를 딕셔너리 형식으로 변환
    history = []
    for msg in session_data.get("messages", []):
        if hasattr(msg, "type") and msg.type == "human":
            history.append({"role": "user", "content": msg.content})
        elif hasattr(msg, "type") and msg.type == "ai":
            # 에이전트 메시지 분리
            if hasattr(msg, "name") and msg.name:
                history.append({"role": "agent", "name": msg.name, "content": msg.content})
            else:
                history.append({"role": "assistant", "content": msg.content})
    
    return history

def delete_session(session_id: str):
    """지정된 세션을 삭제합니다."""
    # 세션이 현재 세션인지 확인
    is_current = session_id == st.session_state.thread_id
    
    # 세션 삭제
    success = st.session_state.session_manager.delete_session(session_id)
    if success:
        logger.info(f"세션 {session_id} 삭제됨")
        
        # 현재 세션이 삭제된 경우 새 세션 생성
        if is_current:
            st.session_state.thread_id = str(uuid.uuid4())
            st.session_state.history = []
            st.success("✅ 현재 세션이 삭제되었습니다. 새 세션으로 전환합니다.")
        else:
            st.success(f"✅ 세션 '{session_id[:8]}...'이(가) 삭제되었습니다!")
        
        st.rerun()
    else:
        logger.warning(f"존재하지 않는 세션을 삭제하려고 시도함: {session_id}")
        st.error("❌ 세션 삭제에 실패했습니다!")

def format_timestamp(timestamp: float) -> str:
    """타임스탬프를 읽기 쉬운 형식으로 변환합니다."""
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

# --- 함수 정의 부분 ---
def print_message():
    """
    채팅 기록을 화면에 출력합니다.
    """
    for message in st.session_state.history:
        if message["role"] == "user":
            st.chat_message("user").markdown(message["content"])
        elif message["role"] == "assistant":
            st.chat_message("assistant").markdown(message["content"])
        elif message["role"] == "agent":
            with st.chat_message("assistant"):
                st.info(f"**{message['name']}**: {message['content']}")


def get_streaming_callback(response_placeholder):
    """
    스트리밍 콜백 함수를 생성합니다.
    
    Args:
        response_placeholder: 응답을 표시할 Streamlit 컴포넌트
    
    Returns:
        callback_func: 스트리밍 콜백 함수
    """
    accumulated_text = []
    
    def callback_func(chunk):
        nonlocal accumulated_text
        
        # 청크가 메시지인 경우
        if isinstance(chunk, dict) and "messages" in chunk:
            messages = chunk["messages"]
            if messages and len(messages) > 0:
                last_message = messages[-1]
                if hasattr(last_message, 'content'):
                    content = last_message.content
                    accumulated_text.append(content)
                    response_placeholder.markdown("".join(accumulated_text))
        
        # 청크가 AIMessageChunk인 경우
        elif isinstance(chunk, AIMessageChunk):
            if chunk.content:
                accumulated_text.append(chunk.content)
                response_placeholder.markdown("".join(accumulated_text))
                
        # 청크가 다른 형태의 메시지인 경우
        elif isinstance(chunk, dict) and "content" in chunk:
            accumulated_text.append(chunk["content"])
            response_placeholder.markdown("".join(accumulated_text))
        
        return None
    
    return callback_func, accumulated_text


async def process_query_streaming(query: str, response_placeholder, timeout_seconds=60) -> Optional[str]:
    """
    사용자 질문을 처리하고 응답을 스트리밍 방식으로 생성합니다.
    
    Args:
        query: 사용자가 입력한 질문 텍스트
        response_placeholder: 응답을 표시할 Streamlit 컴포넌트
        timeout_seconds: 응답 생성 제한 시간(초)
    
    Returns:
        final_text: 최종 응답 텍스트
    """
    start_time = time.time()  # 시작 시간 기록
    
    try:
        if st.session_state.graph:
            # 그래프 호출
            logger.info(f"사용자 쿼리 처리 시작: '{query[:50]}'..." if len(query) > 50 else query)
            
            # 스트리밍 방식으로 호출
            try:
                inputs = {"messages": [HumanMessage(content=query)]}
                config = RunnableConfig(
                    recursion_limit=100,
                    thread_id=st.session_state.thread_id
                )
                
                # 간단한 접근 방식: 비동기로 먼저 전체 응답을 받음
                response = await asyncio.wait_for(
                    st.session_state.graph.ainvoke(inputs),
                    timeout=timeout_seconds
                )
                
                # 마지막 메시지 추출
                if "messages" in response and response["messages"]:
                    final_text = response["messages"][-1].content
                    
                    # 사용자 설정 워드 딜레이 가져오기
                    word_delay = st.session_state.get("word_delay", 0.01)
                    
                    # 응답 텍스트를 단어 단위로 스트리밍처럼 표시 (실제 스트리밍 대신 시뮬레이션)
                    words = final_text.split()
                    current_text = []
                    
                    for word in words:
                        current_text.append(word)
                        display_text = " ".join(current_text)
                        response_placeholder.markdown(display_text)
                        # 단어 사이 사용자 설정 딜레이 적용
                        await asyncio.sleep(word_delay)
                    
                    # 처리 시간 계산 및 표시
                    end_time = time.time()
                    processing_time = end_time - start_time
                    processing_time_msg = f"\n\n*응답 처리 시간: {processing_time:.2f}초*"
                    
                    # 최종 텍스트에 처리 시간 추가
                    final_text_with_time = final_text + processing_time_msg
                    response_placeholder.markdown(final_text_with_time)
                    
                    logger.info(f"쿼리 처리 완료: '{query[:30]}...', 처리 시간: {processing_time:.2f}초")
                    return final_text_with_time
                else:
                    logger.warning("응답 메시지가 없습니다.")
                    error_msg = "죄송합니다. 응답을 생성하지 못했습니다."
                    
                    # 처리 시간 계산 및 표시
                    end_time = time.time()
                    processing_time = end_time - start_time
                    error_msg_with_time = f"{error_msg}\n\n*응답 처리 시간: {processing_time:.2f}초*"
                    
                    response_placeholder.markdown(error_msg_with_time)
                    return error_msg_with_time
                
            except asyncio.TimeoutError:
                error_msg = f"⏱️ 요청 시간이 {timeout_seconds}초를 초과했습니다. 나중에 다시 시도해 주세요."
                logger.error(error_msg)
                
                # 처리 시간 계산 및 표시
                end_time = time.time()
                processing_time = end_time - start_time
                error_msg_with_time = f"{error_msg}\n\n*응답 처리 시간: {processing_time:.2f}초*"
                
                response_placeholder.markdown(error_msg_with_time)
                return error_msg_with_time
            
            except Exception as e:
                import traceback
                error_msg = f"스트리밍 처리 중 오류: {str(e)}"
                logger.error(error_msg)
                logger.error(traceback.format_exc())
                
                # 처리 시간 계산 및 표시
                end_time = time.time()
                processing_time = end_time - start_time
                error_msg_with_time = f"죄송합니다. 오류가 발생했습니다: {str(e)}\n\n*응답 처리 시간: {processing_time:.2f}초*"
                
                response_placeholder.markdown(error_msg_with_time)
                return error_msg_with_time
        else:
            logger.error("그래프가 초기화되지 않았습니다.")
            error_msg = "시스템이 아직 초기화 중입니다. 잠시 후 다시 시도해주세요."
            
            # 처리 시간 계산 및 표시
            end_time = time.time()
            processing_time = end_time - start_time
            error_msg_with_time = f"{error_msg}\n\n*응답 처리 시간: {processing_time:.2f}초*"
            
            response_placeholder.markdown(error_msg_with_time)
            return error_msg_with_time
    except Exception as e:
        import traceback
        error_msg = f"쿼리 처리 중 오류 발생: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        # 처리 시간 계산 및 표시
        end_time = time.time()
        processing_time = end_time - start_time
        error_msg_with_time = f"죄송합니다. 오류가 발생했습니다: {str(e)}\n\n*응답 처리 시간: {processing_time:.2f}초*"
        
        response_placeholder.markdown(error_msg_with_time)
        return error_msg_with_time


async def process_query(query: str) -> Optional[str]:
    """
    사용자 질문을 처리하고 응답을 생성합니다. (비스트리밍 방식)
    
    Args:
        query: 사용자가 입력한 질문 텍스트
    
    Returns:
        response_content: 최종 응답 텍스트
    """
    start_time = time.time()  # 시작 시간 기록
    
    try:
        if st.session_state.graph:
            # 그래프 호출
            logger.info(f"사용자 쿼리 처리 시작: '{query[:50]}'..." if len(query) > 50 else query)
            
            inputs = {"messages": [HumanMessage(content=query)]}
            response = await st.session_state.graph.ainvoke(inputs)
            
            # 응답 처리
            if "messages" in response:
                if response["messages"]:
                    last_message = response["messages"][-1]
                    response_content = last_message.content
                    
                    # 처리 시간 계산 및 표시
                    end_time = time.time()
                    processing_time = end_time - start_time
                    response_content_with_time = f"{response_content}\n\n*응답 처리 시간: {processing_time:.2f}초*"
                    
                    logger.info(f"쿼리 처리 완료: '{query[:30]}...', 처리 시간: {processing_time:.2f}초")
                    return response_content_with_time
                else:
                    logger.warning("응답 메시지가 없습니다.")
                    # 처리 시간 계산 및 표시
                    end_time = time.time()
                    processing_time = end_time - start_time
                    error_msg = f"죄송합니다. 응답을 생성하지 못했습니다.\n\n*응답 처리 시간: {processing_time:.2f}초*"
                    return error_msg
            else:
                logger.warning("응답에 'messages' 키가 없습니다.")
                # 처리 시간 계산 및 표시
                end_time = time.time()
                processing_time = end_time - start_time
                error_msg = f"죄송합니다. 응답 형식이 올바르지 않습니다.\n\n*응답 처리 시간: {processing_time:.2f}초*"
                return error_msg
        else:
            logger.error("그래프가 초기화되지 않았습니다.")
            # 처리 시간 계산 및 표시
            end_time = time.time()
            processing_time = end_time - start_time
            error_msg = f"시스템이 아직 초기화 중입니다. 잠시 후 다시 시도해주세요.\n\n*응답 처리 시간: {processing_time:.2f}초*"
            return error_msg
    except Exception as e:
        import traceback
        error_msg = f"쿼리 처리 중 오류 발생: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        # 처리 시간 계산 및 표시
        end_time = time.time()
        processing_time = end_time - start_time
        error_msg_with_time = f"죄송합니다. 오류가 발생했습니다: {str(e)}\n\n*응답 처리 시간: {processing_time:.2f}초*"
        
        return error_msg_with_time


async def initialize_session():
    """
    세션을 초기화합니다.
    
    Returns:
        bool: 초기화 성공 여부
    """
    try:
        # 그래프 초기화
        logger.info("세션 초기화 시작")
        st.session_state.graph = get_smarthome_graph()
        st.session_state.session_initialized = True
        logger.info("세션 초기화 완료")
        return True
    except Exception as e:
        import traceback
        error_msg = f"세션 초기화 중 오류 발생: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return False


# --- 사이드바 구성 ---
with st.sidebar:
    st.header("📊 시스템 정보")
    
    # 시스템 상태 표시
    initialization_status = "✅ 초기화됨" if st.session_state.session_initialized else "🔄 초기화 중..."
    st.write(f"시스템 상태: {initialization_status}")
    st.write(f"현재 세션 ID: {st.session_state.thread_id[:8]}...")
    
    # 세션 관리 섹션
    st.divider()
    st.subheader("💾 세션 관리")
    
    # 새 세션 생성 버튼
    if st.button("➕ 새 세션 생성", use_container_width=True):
        create_new_session()
    
    # 이전 세션 목록
    try:
        sessions = st.session_state.session_manager.list_sessions()
        if sessions:
            st.write("---")
            st.subheader("📋 저장된 세션 목록")
            
            # 페이지네이션 관련 세션 상태 초기화
            if "session_page" not in st.session_state:
                st.session_state.session_page = 0
            
            # 페이지당 세션 수
            sessions_per_page = 3
            
            # 세션 ID 목록을 생성 (가장 최근에 업데이트된 순으로 정렬)
            sorted_sessions = sorted(
                sessions.items(),
                key=lambda x: x[1].get('updated_at', 0),
                reverse=True
            )
            
            # 현재 페이지에 표시할 세션 목록
            total_pages = (len(sorted_sessions) + sessions_per_page - 1) // sessions_per_page
            start_idx = st.session_state.session_page * sessions_per_page
            end_idx = min(start_idx + sessions_per_page, len(sorted_sessions))
            
            # 현재 페이지 세션 표시
            for session_id, info in sorted_sessions[start_idx:end_idx]:
                # 현재 세션 표시
                is_current = session_id == st.session_state.thread_id
                is_active_tab = session_id in st.session_state.active_tabs
                
                # 세션 라벨 구성
                status_indicator = ""
                if is_current:
                    status_indicator = "🟢 "  # 현재 세션
                elif is_active_tab:
                    status_indicator = "🔵 "  # 열린 탭
                
                session_label = f"{status_indicator}{session_id[:8]}... - 메시지 {info.get('message_count', 0)}개"
                
                with st.expander(session_label):
                    # 세션 메타데이터 표시
                    if "created_at" in info:
                        st.write(f"생성일시: {format_timestamp(info['created_at'])}")
                    if "updated_at" in info:
                        st.write(f"최종수정: {format_timestamp(info['updated_at'])}")
                    
                    # 세션 관리 버튼
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # 열기/전환 버튼
                        if is_active_tab:
                            if st.button(f"📂 전환", key=f"switch_{session_id}", use_container_width=True):
                                switch_tab(session_id)
                        else:
                            if st.button(f"📂 열기", key=f"load_{session_id}", use_container_width=True):
                                load_session(session_id)
                    
                    with col2:
                        # 닫기 버튼 (활성 탭일 경우에만)
                        if is_active_tab and not is_current:
                            if st.button(f"🔒 닫기", key=f"close_{session_id}", use_container_width=True):
                                close_tab(session_id)
                    
                    with col3:
                        # 삭제 버튼
                        if st.button(f"🗑️ 삭제", key=f"delete_{session_id}", use_container_width=True):
                            delete_session(session_id)
            
            # 페이지네이션 UI
            if total_pages > 1:
                st.write("---")
                pagination_cols = st.columns(min(total_pages + 2, 9))  # 최대 7개의 페이지 버튼 + 이전/다음 버튼
                
                # 이전 페이지 버튼
                with pagination_cols[0]:
                    if st.button("◀", key="prev_page", disabled=(st.session_state.session_page <= 0)):
                        st.session_state.session_page = max(0, st.session_state.session_page - 1)
                        st.rerun()
                
                # 페이지 번호 버튼
                max_visible_pages = min(total_pages, 7)  # 한 번에 최대 7개의 페이지 번호만 표시
                
                # 현재 페이지 주변의 페이지 번호 표시 로직
                if total_pages <= max_visible_pages:
                    # 페이지 수가 적으면 모든 페이지 표시
                    page_range = range(total_pages)
                else:
                    # 현재 페이지 주변의 페이지만 표시
                    half_visible = max_visible_pages // 2
                    if st.session_state.session_page < half_visible:
                        # 처음 페이지에 가까우면
                        page_range = range(max_visible_pages)
                    elif st.session_state.session_page >= total_pages - half_visible:
                        # 마지막 페이지에 가까우면
                        page_range = range(total_pages - max_visible_pages, total_pages)
                    else:
                        # 중간 페이지면
                        page_range = range(st.session_state.session_page - half_visible, 
                                          st.session_state.session_page + half_visible + 1)
                
                for i, page_idx in enumerate(page_range, 1):
                    with pagination_cols[i]:
                        # 현재 페이지는 강조 표시
                        page_num = page_idx + 1
                        if page_idx == st.session_state.session_page:
                            st.markdown(f"**{page_num}**")
                        else:
                            if st.button(f"{page_num}", key=f"page_{page_idx}"):
                                st.session_state.session_page = page_idx
                                st.rerun()
                
                # 다음 페이지 버튼
                with pagination_cols[-1]:
                    if st.button("▶", key="next_page", disabled=(st.session_state.session_page >= total_pages - 1)):
                        st.session_state.session_page = min(total_pages - 1, st.session_state.session_page + 1)
                        st.rerun()
                
                # 현재 페이지 정보 표시
                st.write(f"페이지: {st.session_state.session_page + 1}/{total_pages}")
        else:
            st.info("저장된 세션이 없습니다.")
    except Exception as e:
        logger.error(f"세션 목록 조회 실패: {str(e)}")
        st.error(f"세션 목록을 불러올 수 없습니다: {str(e)}")
    
    # 구분선
    st.divider()
    
    # 시스템 정보 확장 (에이전트 정보)
    if st.session_state.session_initialized:
        # 모델 정보
        st.subheader("🤖 에이전트 정보")
        
        # 환경 변수에서 모델 정보 가져오기
        model_name = os.getenv("MODEL_NAME", "gemini-2.5-pro-exp-03-25")
        
        # 에이전트 정보 표시
        st.write(f"🔹 **슈퍼바이저 모델**: {model_name}")
        
        # 에이전트 그래프에서 에이전트 수 가져오기
        try:
            from agents.supervisor_agent import members
            agent_count = len(members)
            st.write(f"🔹 **총 에이전트 수**: {agent_count}개")
            
            # 에이전트 목록
            with st.expander("에이전트 목록 보기"):
                for i, agent in enumerate(members, 1):
                    st.write(f"{i}. **{agent}**")
        except ImportError:
            st.write("🔹 **에이전트 정보를 불러올 수 없습니다.**")
        
        # MCP 서버 정보 표시
        with st.expander("🔌 MCP 서버 및 도구 정보"):
            try:
                # MCP 정보 가져오기
                if "mcp_info" not in st.session_state:
                    with st.spinner("MCP 서버 정보 가져오는 중..."):
                        try:
                            # MCP 클라이언트 설정 정보 가져오기
                            from agents.robot_cleaner_agent import _mcp_client
                            
                            # 만약 MCP 클라이언트가 초기화되지 않았으면 초기화
                            if _mcp_client is None:
                                st.session_state.mcp_info = {"status": "not_initialized"}
                            else:
                                # MCP 클라이언트가 이미 초기화되어 있음
                                st.session_state.mcp_info = {"status": "initialized"}
                                
                                # 서버 설정 가져오기
                                if hasattr(_mcp_client, "servers"):
                                    st.session_state.mcp_info["servers"] = _mcp_client.servers
                                
                                # 도구 정보 가져오기 (비동기 함수 호출)
                                try:
                                    tools_result = st.session_state.event_loop.run_until_complete(get_tools_with_details())
                                    st.session_state.mcp_info["tools_count"] = len(tools_result)
                                    st.session_state.mcp_info["tools"] = tools_result
                                except Exception as e:
                                    st.session_state.mcp_info["tools_error"] = str(e)
                        except Exception as e:
                            st.session_state.mcp_info = {"status": "error", "error": str(e)}
                
                # MCP 정보 표시
                mcp_info = st.session_state.get("mcp_info", {})
                
                if mcp_info.get("status") == "not_initialized":
                    st.warning("MCP 클라이언트가 아직 초기화되지 않았습니다. 로봇청소기 관련 질문을 하면 자동으로 초기화됩니다.")
                
                elif mcp_info.get("status") == "error":
                    st.error(f"MCP 정보 가져오기 실패: {mcp_info.get('error', '알 수 없는 오류')}")
                
                elif mcp_info.get("status") == "initialized":
                    st.success("MCP 클라이언트가 초기화되어 있습니다.")
                    
                    # 서버 정보 표시
                    st.write("##### MCP 서버 정보")
                    if "servers" in mcp_info:
                        for server_name, server_info in mcp_info["servers"].items():
                            st.write(f"- **{server_name}**: {server_info.get('url', '알 수 없음')}")
                    else:
                        st.write("서버 정보를 가져올 수 없습니다.")
                    
                    # 도구 정보 표시
                    st.write("##### MCP 도구 정보")
                    if "tools_error" in mcp_info:
                        st.error(f"도구 정보 가져오기 실패: {mcp_info['tools_error']}")
                    elif "tools_count" in mcp_info:
                        st.write(f"총 **{mcp_info['tools_count']}개**의 MCP 도구가 있습니다.")
                        
                        # 도구 목록 표시
                        if "tools" in mcp_info and mcp_info["tools"]:
                            tool_list = []
                            for i, tool in enumerate(mcp_info["tools"], 1):
                                tool_name = getattr(tool, "name", f"Tool-{i}")
                                tool_list.append(tool_name)
                            
                            # 도구 목록을 깔끔하게 표시
                            st.write("도구 목록:")
                            cols = st.columns(2)
                            mid_point = len(tool_list) // 2 + len(tool_list) % 2
                            
                            with cols[0]:
                                for i, tool in enumerate(tool_list[:mid_point], 1):
                                    st.write(f"{i}. {tool}")
                            
                            with cols[1]:
                                for i, tool in enumerate(tool_list[mid_point:], mid_point+1):
                                    st.write(f"{i}. {tool}")
                    else:
                        st.write("도구 정보를 가져올 수 없습니다.")
                
                # 수동 초기화 버튼
                if st.button("MCP 정보 새로고침", key="refresh_mcp"):
                    try:
                        with st.spinner("MCP 서버 연결 및 도구 정보 새로고침 중..."):
                            # 비동기 함수 호출
                            st.session_state.mcp_info = st.session_state.event_loop.run_until_complete(refresh_mcp_info())
                            st.success("MCP 정보가 새로고침되었습니다.")
                    except Exception as e:
                        st.error(f"MCP 정보 새로고침 실패: {str(e)}")
                        st.session_state.mcp_info = {"status": "error", "error": str(e)}
                    st.rerun()
                
            except Exception as e:
                st.error(f"MCP 정보 표시 중 오류 발생: {str(e)}")
    
    # 구분선
    st.divider()
    
    # 그래프 시각화 표시 (접었다 펼 수 있는 기능)
    if st.session_state.session_initialized:
        if st.checkbox("🔄 에이전트 그래프 표시", value=True):
            try:
                # 그래프 이미지 생성
                with st.spinner("그래프 이미지 생성 중..."):
                    mermaid_graph = get_mermaid_graph()
                    st.image(mermaid_graph, use_container_width=True)
            except Exception as e:
                st.error(f"그래프 이미지 생성 실패: {str(e)}")
    else:
        st.info("시스템 초기화 중입니다. 잠시만 기다려주세요...")
    
    # 구분선
    st.divider()
    
    # 시스템 설정 섹션
    st.subheader("⚙️ 시스템 설정")
    
    # 스트리밍 모드 토글
    st.session_state.streaming_mode = st.toggle("스트리밍 응답 활성화", value=True)
    
    # 응답 속도 조절 (단어 표시 간격)
    if st.session_state.get("streaming_mode", True):
        if "word_delay" not in st.session_state:
            st.session_state.word_delay = 0.01
        
        st.session_state.word_delay = st.slider(
            "응답 속도 조절", 
            min_value=0.0, 
            max_value=0.05, 
            value=st.session_state.word_delay,
            step=0.01,
            format="%.2f초"
        )

# --- 기본 세션 초기화 (초기화되지 않은 경우) ---
if not st.session_state.session_initialized:
    init_placeholder = st.empty()
    with init_placeholder.container():
        st.info("🔄 스마트홈 에이전트 시스템을 초기화 중입니다. 잠시만 기다려주세요...")
        progress_bar = st.progress(0)
        
        # 진행 상태 업데이트
        progress_bar.progress(30)
        
        # 초기화 실행
        success = st.session_state.event_loop.run_until_complete(initialize_session())
        
        # 진행 상태 업데이트
        progress_bar.progress(100)
        
        if success:
            st.success("✅ 스마트홈 에이전트 시스템이 성공적으로 초기화되었습니다!")
            # 초기화 완료 플래그 설정
            st.session_state.initialization_completed = True
        else:
            st.error("❌ 시스템 초기화에 실패했습니다. 페이지를 새로고침해주세요.")
        
    # 1초 후 페이지 자동 새로고침
    if st.session_state.initialization_completed and not st.session_state.get('reloaded', False):
        import time
        time.sleep(1)
        st.session_state.reloaded = True
        st.rerun()

# --- 세션이 종료될 때 현재 세션 저장 ---
def save_on_exit():
    if st.session_state.session_initialized and st.session_state.history:
        save_current_session()

# 종료 이벤트 핸들러 등록 (Streamlit에서는 직접 지원하지 않지만, 세션이 변경될 때마다 저장)
if st.session_state.session_initialized and st.session_state.history:
    # 세션 데이터가 변경될 때마다 저장 (페이지 리로드 시)
    save_current_session()

# --- 탭 인터페이스 구현 ---
# 활성화된 탭이 있는 경우 탭 인터페이스 표시
if st.session_state.active_tabs:
    # 탭 이름 목록 생성
    tab_labels = []
    for tab_id in st.session_state.active_tabs:
        # 현재 세션인 경우 표시
        if tab_id == st.session_state.thread_id:
            tab_labels.append(f"🏠 현재 ({tab_id[:8]}...)")
        else:
            # 세션 메시지 수 가져오기
            try:
                sessions = st.session_state.session_manager.list_sessions()
                msg_count = sessions.get(tab_id, {}).get("message_count", 0)
                tab_labels.append(f"📜 {tab_id[:8]}... ({msg_count}개)")
            except:
                tab_labels.append(f"📜 {tab_id[:8]}...")
    
    # 탭 생성
    tabs = st.tabs(tab_labels)
    
    # 각 탭 내용 채우기
    for i, tab_id in enumerate(st.session_state.active_tabs):
        with tabs[i]:
            # 현재 활성 세션으로 설정 (탭 클릭 시)
            if st.session_state.active_session_id != tab_id:
                st.session_state.active_session_id = tab_id
            
            # 현재 세션이 아닌 경우 읽기 전용 안내와 닫기 버튼 표시
            if tab_id != st.session_state.thread_id:
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.info("⚠️ 이 세션은 읽기 전용입니다")
                with col2:
                    if st.button("❌ 닫기", key=f"tab_close_{tab_id}", help="이 탭 닫기", use_container_width=True):
                        close_tab(tab_id)
                        st.rerun()
            
            # 지정된 세션의 대화 기록 표시
            history = get_session_history(tab_id)
            for message in history:
                if message["role"] == "user":
                    st.chat_message("user").markdown(message["content"])
                elif message["role"] == "assistant":
                    st.chat_message("assistant").markdown(message["content"])
                elif message["role"] == "agent":
                    with st.chat_message("assistant"):
                        st.info(f"**{message['name']}**: {message['content']}")
else:
    # --- 대화 기록 출력 ---
    print_message()

# --- 사용자 입력 및 처리 ---
user_query = st.chat_input("💬 스마트홈 관리 명령이나 질문을 입력하세요")
if user_query:
    if st.session_state.session_initialized:
        # 사용자 메시지 표시
        st.chat_message("user").markdown(user_query)
        
        # 응답 생성 중 표시
        with st.chat_message("assistant"):
            response_placeholder = st.empty()
            
            # 사용자 선택에 따라 스트리밍 또는 일반 방식으로 처리
            if st.session_state.get("streaming_mode", True):
                # 스트리밍 방식
                with st.spinner("🤖 스마트홈 시스템이 응답을 생성하고 있습니다..."):
                    response = st.session_state.event_loop.run_until_complete(
                        process_query_streaming(user_query, response_placeholder)
                    )
            else:
                # 일반 방식
                with st.spinner("🤖 스마트홈 시스템이 응답을 생성하고 있습니다..."):
                    response = st.session_state.event_loop.run_until_complete(
                        process_query(user_query)
                    )
                    response_placeholder.markdown(response)
        
        # 대화 기록 저장
        st.session_state.history.append({"role": "user", "content": user_query})
        st.session_state.history.append({"role": "assistant", "content": response})
        
        # 세션 자동 저장
        save_current_session()
        
        # 페이지 리로드
        st.rerun()
    else:
        st.warning("⏳ 시스템이 아직 초기화 중입니다. 잠시 후 다시 시도해주세요.")
