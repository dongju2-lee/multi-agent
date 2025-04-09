import streamlit as st
import time
import asyncio
import uuid
from typing import Optional, List, Dict, Any
import datetime

from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.messages.ai import AIMessageChunk
from langchain_core.runnables import RunnableConfig
from logging_config import setup_logger
from graphs.smarthome_graph import get_smarthome_graph
from session_manager import create_session_manager

# 로거 설정
logger = setup_logger("chatbot_page")

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
    
    if role == "user":
        return HumanMessage(content=content)
    elif role == "assistant":
        return AIMessage(content=content)
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


def initialize_chatbot():
    """챗봇 기능을 초기화합니다."""
    try:
        # 이벤트 루프 초기화
        if "event_loop" not in st.session_state:
            st.session_state.event_loop = asyncio.new_event_loop()
        
        # 그래프 초기화
        if "graph" not in st.session_state:
            st.session_state.graph = get_smarthome_graph()
        
        # 세션 관리자 초기화
        if "session_manager" not in st.session_state:
            st.session_state.session_manager = create_session_manager()
        
        # 스레드 ID 생성
        if "thread_id" not in st.session_state:
            st.session_state.thread_id = str(uuid.uuid4())
        
        # 대화 기록 초기화
        if "history" not in st.session_state:
            st.session_state.history = []
            
        return True
    except Exception as e:
        logger.error(f"챗봇 초기화 실패: {str(e)}")
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
        if is_initialized and st.session_state.history:
            st.markdown("---")
            st.subheader("💾 현재 세션 정보")
            st.write(f"세션 ID: {st.session_state.thread_id[:8]}...")
            st.write(f"메시지 수: {len(st.session_state.history)}")
            
            if st.button("세션 저장", use_container_width=True):
                if save_current_session():
                    st.success("✅ 세션이 저장되었습니다!")
                else:
                    st.error("❌ 세션 저장에 실패했습니다!")
        
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
            from page_list.helpers import display_agent_graph
            display_agent_graph()
        
        # MCP 서버 정보 표시
        if st.checkbox("MCP 서버 정보 표시"):
            from page_list.helpers import display_mcp_servers_info
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
    
    logger.info("채팅봇 페이지가 로드되었습니다.") 