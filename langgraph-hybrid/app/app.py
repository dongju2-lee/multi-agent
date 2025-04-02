import os
import streamlit as st
import asyncio
import nest_asyncio
from typing import Optional
import uuid
import json
import sys
import time

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

# 환경 변수 로드
load_dotenv(override=True)

# 로거 설정
logger = setup_logger("streamlit_app")

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
    st.write(f"세션 ID: {st.session_state.thread_id[:8]}...")
    
    # 시스템 정보 확장 (에이전트 정보)
    if st.session_state.session_initialized:
        # 모델 정보
        st.write("---")
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
    
    # 대화 초기화 버튼
    if st.button("🔄 대화 초기화", use_container_width=True):
        st.session_state.history = []
        st.session_state.thread_id = str(uuid.uuid4())
        st.success("대화가 초기화되었습니다.")
        st.rerun()


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
        
        # 페이지 리로드
        st.rerun()
    else:
        st.warning("⏳ 시스템이 아직 초기화 중입니다. 잠시 후 다시 시도해주세요.")
