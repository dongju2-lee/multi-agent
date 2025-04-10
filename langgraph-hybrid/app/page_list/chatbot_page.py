import streamlit as st
import time
import asyncio
import uuid
from typing import Optional, List, Dict, Any
import datetime
import os
import sys
import requests
import json

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.messages.ai import AIMessageChunk
from langchain_core.runnables import RunnableConfig
from logging_config import setup_logger
from graphs.smarthome_graph import get_smarthome_graph, get_mermaid_graph
from session_manager import create_session_manager, get_session_manager

# 로거 설정
logger = setup_logger("chatbot_page")

LANGFUSE_SECRET_KEY= os.environ.get("LANGFUSE_SECRET_KEY")
LANGFUSE_PUBLIC_KEY= os.environ.get("LANGFUSE_PUBLIC_KEY")
LANGFUSE_HOST= os.environ.get("LANGFUSE_HOST")

from langfuse.callback import CallbackHandler
langfuse_handler = CallbackHandler(
    public_key=LANGFUSE_PUBLIC_KEY,
    secret_key=LANGFUSE_SECRET_KEY,
    host=LANGFUSE_HOST
)
logger.info(f"langfuse셋팅 :: LANGFUSE_SECRET_KEY : {LANGFUSE_SECRET_KEY} :: LANGFUSE_PUBLIC_KEY : {LANGFUSE_PUBLIC_KEY} :: LANGFUSE_HOST : {LANGFUSE_HOST} ")
from langfuse.callback import CallbackHandler
langfuse_handler = CallbackHandler()

# --- 세션 관리 함수들 ---
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
    if "session_manager" not in st.session_state or "thread_id" not in st.session_state:
        logger.warning("세션 매니저 또는 스레드 ID가 초기화되지 않았습니다")
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
    if "session_manager" not in st.session_state:
        logger.warning("세션 매니저가 초기화되지 않았습니다")
        return False
        
    # 세션 데이터 가져오기
    session_data = st.session_state.session_manager.get_session(session_id)
    if not session_data:
        logger.warning(f"존재하지 않는 세션을 불러오려고 시도함: {session_id}")
        st.error("❌ 세션을 불러올 수 없습니다!")
        return False
    
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
    
    # 세션 상태 업데이트
    st.session_state.thread_id = session_id
    st.session_state.history = history
    
    logger.info(f"세션 {session_id} 불러오기 완료 (메시지 수: {len(history)}개)")
    return True

def format_timestamp(timestamp: float) -> str:
    """타임스탬프를 읽기 쉬운 형식으로 변환합니다."""
    dt = datetime.datetime.fromtimestamp(timestamp)
    return dt.strftime("%Y-%m-%d %H:%M:%S")

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
                    st.session_state.graph.ainvoke(inputs,config={"callbacks": [langfuse_handler]}),
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
            response = await st.session_state.graph.ainvoke(inputs,config={"callbacks": [langfuse_handler]})
            
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


def initialize_chatbot():
    """
    챗봇 기능을 초기화합니다.
    이벤트 루프, 그래프, 세션 매니저 및 대화 기록을 설정합니다.
    """
    try:
        logger.info("챗봇 초기화 시작")
        
        # 이벤트 루프
        if "event_loop" not in st.session_state:
            import asyncio
            logger.info("이벤트 루프 초기화")
            st.session_state.event_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(st.session_state.event_loop)
        
        # 그래프 초기화 (이미 없는 경우에만)
        if "graph" not in st.session_state:
            logger.info("그래프 초기화")
            from graphs.smarthome_graph import get_smarthome_graph
            st.session_state.graph = get_smarthome_graph()
        
        # 세션 매니저 초기화 (이미 없는 경우에만)
        if "session_manager" not in st.session_state:
            logger.info("세션 매니저 초기화")
            from session_manager import get_session_manager
            manager_type = os.environ.get("SESSION_MANAGER_TYPE", "in_memory")
            st.session_state.session_manager = get_session_manager(manager_type)
        
        # 스레드 ID 생성 (이미 없는 경우에만)
        if "thread_id" not in st.session_state:
            logger.info("대화 스레드 ID 초기화")
            st.session_state.thread_id = str(uuid.uuid4())
        
        # 대화 기록 초기화 (이미 없는 경우에만)
        if "history" not in st.session_state:
            logger.info("대화 기록 초기화")
            st.session_state.history = []
        
        # 초기화 상태 설정
        logger.info("챗봇 초기화 완료")
        return True
    except Exception as e:
        import traceback
        logger.error(f"챗봇 초기화 실패: {str(e)}")
        logger.error(traceback.format_exc())
        return False


def chatbot_page():
    """
    멀티에이전트 스마트홈 시스템 채팅봇 페이지입니다.
    """
    st.title("💬 스마트홈 채팅봇")
    st.markdown("---")
    
    # 채팅봇 소개
    st.markdown("""
    자연어로 스마트홈 시스템과 대화할 수 있는 인터페이스입니다.  
    명령을 내리거나 질문을 하면 멀티에이전트 시스템이 적절한 응답을 제공합니다.
    """)
    
    # 챗봇 초기화
    is_initialized = initialize_chatbot()
    
    # 세션 관리 설정
    with st.sidebar:
        # 세션 상태가 있을 때 현재 세션 정보 표시
        if is_initialized:
            st.markdown("---")
            st.subheader("💾 세션 관리")
            
            # 현재 세션 정보 표시
            st.write(f"현재 세션 ID: `{st.session_state.thread_id[:8]}...`")
            st.write(f"메시지 수: {len(st.session_state.history)}")
            
            # 세션 저장 버튼
            if st.button("💾 현재 세션 저장", use_container_width=True):
                if save_current_session():
                    st.success("✅ 세션이 저장되었습니다!")
                else:
                    st.error("❌ 세션 저장에 실패했습니다!")
            
            # 새 세션 생성 버튼
            if st.button("🆕 새 세션 생성", use_container_width=True):
                # 현재 세션 저장
                if st.session_state.history:
                    save_current_session()
                
                # 새 세션 생성
                st.session_state.thread_id = str(uuid.uuid4())
                st.session_state.history = []
                st.success("✅ 새 세션이 생성되었습니다!")
                st.rerun()
            
            # 이전 세션 불러오기
            if "session_manager" in st.session_state:
                try:
                    # 저장된 세션 목록 가져오기
                    sessions = st.session_state.session_manager.list_sessions()
                    
                    if sessions:
                        st.markdown("---")
                        st.subheader("📋 저장된 세션 목록")
                        
                        # 정렬된 세션 목록 생성 (최신순)
                        sorted_sessions = sorted(
                            sessions.items(),
                            key=lambda x: x[1].get('updated_at', 0),
                            reverse=True
                        )
                        
                        # 표시할 세션 수 제한
                        max_sessions = 5
                        visible_sessions = sorted_sessions[:max_sessions]
                        
                        # 세션 목록 표시
                        for session_id, info in visible_sessions:
                            # 현재 세션은 제외
                            if session_id == st.session_state.thread_id:
                                continue
                                
                            # 세션 정보 구성
                            timestamp = format_timestamp(info.get('updated_at', 0))
                            msg_count = info.get('message_count', 0)
                            
                            with st.expander(f"ID: {session_id[:8]}... ({timestamp})"):
                                st.write(f"메시지 수: {msg_count}개")
                                st.write(f"마지막 업데이트: {timestamp}")
                                
                                # 세션 불러오기 버튼
                                if st.button("📂 불러오기", key=f"load_{session_id}", help="이 세션 불러오기"):
                                    if load_session(session_id):
                                        st.success(f"세션 '{session_id[:8]}...'를 불러왔습니다!")
                                        st.rerun()
                        
                        # 더 많은 세션이 있는 경우
                        if len(sorted_sessions) > max_sessions:
                            st.info(f"총 {len(sorted_sessions)}개의 세션 중 {max_sessions}개를 표시하고 있습니다.")
                    else:
                        st.info("저장된 세션이 없습니다.")
                except Exception as e:
                    logger.error(f"세션 목록 조회 실패: {str(e)}")
                    st.error(f"세션 목록을 불러올 수 없습니다: {str(e)}")
        
        # LLM 모델 정보
        st.markdown("---")
        st.subheader("🤖 LLM 모델 정보")
        with st.expander("LLM 모델 세부 정보"):
            st.markdown("""
            - **슈퍼바이저 에이전트**: ChatVertexAI (gemini-pro)
            - **루틴 에이전트**: ChatVertexAI (gemini-pro)
            - **가전제품 에이전트**: ChatVertexAI (gemini-pro)
            - **식품 매니저 에이전트**: ChatVertexAI (gemini-pro)
            - **검색 에이전트**: ChatVertexAI (gemini-pro)
            """)
        
        # 시스템 정보 표시 옵션
        st.markdown("---")
        st.subheader("🔍 시스템 정보")
        
        # 에이전트 그래프 표시
        if st.checkbox("에이전트 그래프 표시"):
            display_agent_graph()
        
        # MCP 서버 정보 표시
        if st.checkbox("MCP 서버 정보 표시"):
            display_mcp_servers_info()
    
    # 대화 기록 출력
    print_message()
    
    # 사용자 입력 처리
    user_query = st.chat_input("💬 스마트홈 관리 명령이나 질문을 입력하세요")
    if user_query:
        if is_initialized:
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
            st.warning("⏳ 시스템을 초기화하는 중 문제가 발생했습니다. 페이지를 새로고침하거나 잠시 후 다시 시도해주세요.")
    
    logger.info("챗봇 페이지가 로드되었습니다.")

def display_agent_graph():
    """에이전트 그래프를 시각화하여 표시합니다."""
    try:
        # 그래프 이미지 생성 (더 긴 타임아웃 설정)
        with st.spinner("그래프 이미지를 생성하는 중입니다. 이 작업은 최대 60초까지 소요될 수 있습니다..."):
            import threading
            import time
            
            # 그래프 이미지 생성 결과를 저장할 변수
            result = {"image": None, "error": None}
            
            # 그래프 이미지 생성 함수
            def generate_graph():
                try:
                    result["image"] = get_mermaid_graph()
                except Exception as e:
                    result["error"] = str(e)
            
            # 스레드 생성 및 시작
            graph_thread = threading.Thread(target=generate_graph)
            graph_thread.daemon = True
            graph_thread.start()
            
            # 최대 60초 대기 (타임아웃 대폭 증가)
            wait_time = 60  # 60초
            start_time = time.time()
            
            # 진행 상황 표시를 위한 진행 바
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            while graph_thread.is_alive() and time.time() - start_time < wait_time:
                # 경과 시간 표시
                elapsed = time.time() - start_time
                progress = min(int((elapsed / wait_time) * 100), 99)
                progress_bar.progress(progress)
                status_text.text(f"그래프 생성 중... ({int(elapsed)}초 경과)")
                time.sleep(0.5)
            
            if graph_thread.is_alive():
                # 시간 초과
                status_text.text("시간 초과, 이미지 생성 중단.")
                st.warning("그래프 이미지 생성 시간이 초과되었습니다(60초). 인터넷 연결 상태를 확인하거나 나중에 다시 시도해주세요.")
                
                # 대체 방안: 네트워크 문제일 수 있으니 다시 시도 버튼 제공
                if st.button("그래프 생성 다시 시도"):
                    st.rerun()
            elif result["error"]:
                # 에러 발생
                status_text.text("오류 발생.")
                st.warning(f"그래프 이미지 생성 실패: {result['error']}")
                
                # 다시 시도 버튼 제공
                if st.button("그래프 생성 다시 시도"):
                    st.rerun()
            else:
                # 이미지 생성 성공
                progress_bar.progress(100)
                status_text.text("그래프 생성 완료!")
                # 이미지 표시
                st.image(result["image"], use_container_width=True)
    except Exception as e:
        st.warning(f"그래프 시각화 실패: {str(e)}")
        
        # 다시 시도 버튼 제공
        if st.button("그래프 생성 다시 시도"):
            st.rerun()

async def refresh_mcp_info():
    """MCP 클라이언트 정보를 새로고침합니다."""
    try:
        logger.info("MCP 정보 새로고침 시작")
        
        # 모든 에이전트에서 도구 관련 함수 임포트
        from agents.induction_agent import get_tools_with_details as get_induction_tools
        from agents.food_manager_agent import get_tools_with_details as get_food_manager_tools
        from agents.microwave_agent import get_tools_with_details as get_microwave_tools
        from agents.refrigerator_agent import get_tools_with_details as get_refrigerator_tools
        from agents.routine_agent import get_tools_with_details as get_routine_tools
        
        # 모든 MCP 클라이언트 정보 저장
        all_mcp_info = {}
        
        # 인덕션 도구
        try:
            induction_tools = await get_induction_tools()
            all_mcp_info["induction"] = {
                "tools": induction_tools,
                "client": True if induction_tools else False
            }
        except Exception as e:
            logger.error(f"인덕션 도구 가져오기 실패: {str(e)}")
            all_mcp_info["induction"] = {"error": str(e)}
        
        # 음식 매니저 도구
        try:
            food_manager_tools = await get_food_manager_tools()
            all_mcp_info["food_manager"] = {
                "tools": food_manager_tools,
                "client": True if food_manager_tools else False
            }
        except Exception as e:
            logger.error(f"음식 매니저 도구 가져오기 실패: {str(e)}")
            all_mcp_info["food_manager"] = {"error": str(e)}
        
        # 전자레인지 도구
        try:
            microwave_tools = await get_microwave_tools()
            all_mcp_info["microwave"] = {
                "tools": microwave_tools,
                "client": True if microwave_tools else False
            }
        except Exception as e:
            logger.error(f"전자레인지 도구 가져오기 실패: {str(e)}")
            all_mcp_info["microwave"] = {"error": str(e)}
        
        # 냉장고 도구
        try:
            refrigerator_tools = await get_refrigerator_tools()
            all_mcp_info["refrigerator"] = {
                "tools": refrigerator_tools,
                "client": True if refrigerator_tools else False
            }
        except Exception as e:
            logger.error(f"냉장고 도구 가져오기 실패: {str(e)}")
            all_mcp_info["refrigerator"] = {"error": str(e)}
        
        # 루틴 도구
        try:
            routine_tools = await get_routine_tools()
            all_mcp_info["routine"] = {
                "tools": routine_tools,
                "client": True if routine_tools else False
            }
        except Exception as e:
            logger.error(f"루틴 도구 가져오기 실패: {str(e)}")
            all_mcp_info["routine"] = {"error": str(e)}
        
        # 모든 도구 수 계산
        total_tools_count = sum(len(info.get("tools", [])) for info in all_mcp_info.values() if "tools" in info)
        logger.info(f"총 {total_tools_count}개의 MCP 도구를 가져왔습니다")
        
        # 결과 반환
        return {
            "status": "initialized",
            "all_mcp_info": all_mcp_info,
            "tools_count": total_tools_count
        }
    except Exception as e:
        logger.error(f"MCP 정보 새로고침 중 오류 발생: {str(e)}")
        return {"status": "error", "error": str(e)}

def display_mcp_servers_info():
    """MCP 서버 정보 및 도구 목록을 동적으로 표시합니다."""
    try:
        st.write("## MCP 서버 목록")
        
        # 로딩 상태 표시
        with st.spinner("MCP 서버 정보를 가져오는 중입니다..."):
            # MCP 정보 가져오기
            if "mcp_info" not in st.session_state or st.button("🔄 MCP 정보 새로고침"):
                # MCP 정보 가져오기
                if "event_loop" in st.session_state:
                    # 이벤트 루프가 이미 존재하는 경우 사용
                    mcp_info = st.session_state.event_loop.run_until_complete(refresh_mcp_info())
                else:
                    # 이벤트 루프가 없는 경우 새로 생성
                    import asyncio
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    mcp_info = loop.run_until_complete(refresh_mcp_info())
                    loop.close()
                
                st.session_state.mcp_info = mcp_info
                
                if mcp_info["status"] == "error":
                    st.error(f"MCP 정보를 가져오는 중 오류가 발생했습니다: {mcp_info['error']}")
                    return
                
                st.success(f"✅ MCP 서버 정보를 성공적으로 가져왔습니다! (총 {mcp_info['tools_count']}개 도구)")
        
        # MCP 정보가 있으면 표시
        if "mcp_info" in st.session_state and st.session_state.mcp_info["status"] == "initialized":
            mcp_info = st.session_state.mcp_info
            
            # 서버 정보 탭 생성
            tabs = st.tabs(["인덕션", "냉장고", "음식 매니저", "전자레인지", "루틴"])
            
            # 인덕션 서버 정보
            with tabs[0]:
                if "induction" in mcp_info["all_mcp_info"]:
                    induction_info = mcp_info["all_mcp_info"]["induction"]
                    if "error" in induction_info:
                        st.error(f"❌ 인덕션 서버 연결 실패: {induction_info['error']}")
                    else:
                        client = induction_info.get("client")
                        tools = induction_info.get("tools", [])
                        
                        # 연결 상태
                        if client:
                            st.success("✅ 인덕션 서버 연결됨")
                            st.write(f"- **URL**: http://0.0.0.0:8002/sse")
                            st.write(f"- **포트**: 8002")
                            st.write(f"- **전송 방식**: sse")
                            
                            # 도구 정보
                            if tools:
                                st.subheader("사용 가능한 도구")
                                for tool in tools:
                                    tool_name = getattr(tool, "name", "")
                                    tool_desc = getattr(tool, "description", "설명 없음")
                                    
                                    with st.expander(f"📲 {tool_name}"):
                                        st.write(f"**설명**: {tool_desc}")
                                        
                                        # 매개변수 정보 표시
                                        try:
                                            params = tool.args
                                            if params:
                                                st.write("**매개변수**:")
                                                for param_name, param_info in params.items():
                                                    param_desc = param_info.get("description", "설명 없음")
                                                    param_type = param_info.get("type", "unknown")
                                                    st.write(f"- **{param_name}** ({param_type}): {param_desc}")
                                        except AttributeError:
                                            st.info("매개변수 정보를 가져올 수 없습니다.")
                            else:
                                st.warning("⚠️ 사용 가능한 도구가 없습니다.")
                        else:
                            st.error("❌ 인덕션 서버 연결 안됨")
                else:
                    st.error("❌ 인덕션 서버 정보를 가져올 수 없습니다.")
            
            # 냉장고 서버 정보
            with tabs[1]:
                if "refrigerator" in mcp_info["all_mcp_info"]:
                    refrigerator_info = mcp_info["all_mcp_info"]["refrigerator"]
                    if "error" in refrigerator_info:
                        st.error(f"❌ 냉장고 서버 연결 실패: {refrigerator_info['error']}")
                    else:
                        client = refrigerator_info.get("client")
                        tools = refrigerator_info.get("tools", [])
                        
                        # 연결 상태
                        if client:
                            st.success("✅ 냉장고 서버 연결됨")
                            st.write(f"- **URL**: http://0.0.0.0:8003/sse")
                            st.write(f"- **포트**: 8003")
                            st.write(f"- **전송 방식**: sse")
                            
                            # 도구 정보
                            if tools:
                                st.subheader("사용 가능한 도구")
                                for tool in tools:
                                    tool_name = getattr(tool, "name", "")
                                    tool_desc = getattr(tool, "description", "설명 없음")
                                    
                                    with st.expander(f"📲 {tool_name}"):
                                        st.write(f"**설명**: {tool_desc}")
                                        
                                        # 매개변수 정보 표시
                                        try:
                                            params = tool.args
                                            if params:
                                                st.write("**매개변수**:")
                                                for param_name, param_info in params.items():
                                                    param_desc = param_info.get("description", "설명 없음")
                                                    param_type = param_info.get("type", "unknown")
                                                    st.write(f"- **{param_name}** ({param_type}): {param_desc}")
                                        except AttributeError:
                                            st.info("매개변수 정보를 가져올 수 없습니다.")
                            else:
                                st.warning("⚠️ 사용 가능한 도구가 없습니다.")
                        else:
                            st.error("❌ 냉장고 서버 연결 안됨")
                else:
                    st.error("❌ 냉장고 서버 정보를 가져올 수 없습니다.")
            
            # 음식 매니저 서버 정보도 같은 방식으로 표시 (생략)
            with tabs[2]:
                if "food_manager" in mcp_info["all_mcp_info"]:
                    food_manager_info = mcp_info["all_mcp_info"]["food_manager"]
                    if "error" in food_manager_info:
                        st.error(f"❌ 음식 매니저 서버 연결 실패: {food_manager_info['error']}")
                    else:
                        client = food_manager_info.get("client")
                        tools = food_manager_info.get("tools", [])
                        
                        # 연결 상태
                        if client:
                            st.success("✅ 음식 매니저 서버 연결됨")
                            st.write(f"- **URL**: http://0.0.0.0:8004/sse")
                            st.write(f"- **포트**: 8004")
                            st.write(f"- **전송 방식**: sse")
                            
                            # 도구 정보
                            if tools:
                                st.subheader("사용 가능한 도구")
                                for tool in tools:
                                    tool_name = getattr(tool, "name", "")
                                    tool_desc = getattr(tool, "description", "설명 없음")
                                    
                                    with st.expander(f"📲 {tool_name}"):
                                        st.write(f"**설명**: {tool_desc}")
                                        
                                        # 매개변수 정보 표시
                                        try:
                                            params = tool.args
                                            if params:
                                                st.write("**매개변수**:")
                                                for param_name, param_info in params.items():
                                                    param_desc = param_info.get("description", "설명 없음")
                                                    param_type = param_info.get("type", "unknown")
                                                    st.write(f"- **{param_name}** ({param_type}): {param_desc}")
                                        except AttributeError:
                                            st.info("매개변수 정보를 가져올 수 없습니다.")
                            else:
                                st.warning("⚠️ 사용 가능한 도구가 없습니다.")
                        else:
                            st.error("❌ 음식 매니저 서버 연결 안됨")
                else:
                    st.error("❌ 음식 매니저 서버 정보를 가져올 수 없습니다.")
            
            # 전자레인지 서버 정보
            with tabs[3]:
                if "microwave" in mcp_info["all_mcp_info"]:
                    microwave_info = mcp_info["all_mcp_info"]["microwave"]
                    if "error" in microwave_info:
                        st.error(f"❌ 전자레인지 서버 연결 실패: {microwave_info['error']}")
                    else:
                        client = microwave_info.get("client")
                        tools = microwave_info.get("tools", [])
                        
                        # 연결 상태
                        if client:
                            st.success("✅ 전자레인지 서버 연결됨")
                            st.write(f"- **URL**: http://0.0.0.0:8005/sse")
                            st.write(f"- **포트**: 8005")
                            st.write(f"- **전송 방식**: sse")
                            
                            # 도구 정보
                            if tools:
                                st.subheader("사용 가능한 도구")
                                for tool in tools:
                                    tool_name = getattr(tool, "name", "")
                                    tool_desc = getattr(tool, "description", "설명 없음")
                                    
                                    with st.expander(f"📲 {tool_name}"):
                                        st.write(f"**설명**: {tool_desc}")
                                        
                                        # 매개변수 정보 표시
                                        try:
                                            params = tool.args
                                            if params:
                                                st.write("**매개변수**:")
                                                for param_name, param_info in params.items():
                                                    param_desc = param_info.get("description", "설명 없음")
                                                    param_type = param_info.get("type", "unknown")
                                                    st.write(f"- **{param_name}** ({param_type}): {param_desc}")
                                        except AttributeError:
                                            st.info("매개변수 정보를 가져올 수 없습니다.")
                            else:
                                st.warning("⚠️ 사용 가능한 도구가 없습니다.")
                        else:
                            st.error("❌ 전자레인지 서버 연결 안됨")
                else:
                    st.error("❌ 전자레인지 서버 정보를 가져올 수 없습니다.")
            
            # 루틴 서버 정보
            with tabs[4]:
                if "routine" in mcp_info["all_mcp_info"]:
                    routine_info = mcp_info["all_mcp_info"]["routine"]
                    if "error" in routine_info:
                        st.error(f"❌ 루틴 서버 연결 실패: {routine_info['error']}")
                    else:
                        client = routine_info.get("client")
                        tools = routine_info.get("tools", [])
                        
                        # 연결 상태
                        if client:
                            st.success("✅ 루틴 서버 연결됨")
                            st.write(f"- **URL**: http://0.0.0.0:8007/sse")
                            st.write(f"- **포트**: 8007")
                            st.write(f"- **전송 방식**: sse")
                            
                            # 도구 정보
                            if tools:
                                st.subheader("사용 가능한 도구")
                                for tool in tools:
                                    tool_name = getattr(tool, "name", "")
                                    tool_desc = getattr(tool, "description", "설명 없음")
                                    
                                    with st.expander(f"📲 {tool_name}"):
                                        st.write(f"**설명**: {tool_desc}")
                                        
                                        # 매개변수 정보 표시
                                        try:
                                            params = tool.args
                                            if params:
                                                st.write("**매개변수**:")
                                                for param_name, param_info in params.items():
                                                    param_desc = param_info.get("description", "설명 없음")
                                                    param_type = param_info.get("type", "unknown")
                                                    st.write(f"- **{param_name}** ({param_type}): {param_desc}")
                                        except AttributeError:
                                            st.info("매개변수 정보를 가져올 수 없습니다.")
                            else:
                                st.warning("⚠️ 사용 가능한 도구가 없습니다.")
                        else:
                            st.error("❌ 루틴 서버 연결 안됨")
                else:
                    st.error("❌ 루틴 서버 정보를 가져올 수 없습니다.")
        else:
            st.warning("⚠️ MCP 서버 정보가 아직 로드되지 않았습니다. '새로고침' 버튼을 클릭하세요.")
    except Exception as e:
        st.error(f"MCP 정보 표시 중 오류 발생: {str(e)}")
        logger.error(f"MCP 정보 표시 중 오류: {str(e)}", exc_info=True) 