import streamlit as st
import asyncio
import nest_asyncio
import json
import os
import requests
import uuid
from datetime import datetime
import time
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from graph import create_smart_home_graph
from langchain_core.messages import HumanMessage

# 환경 변수 로드
load_dotenv(override=True)
MOCK_SERVER_URL = os.getenv("MOCK_SERVER_URL", "http://localhost:8000")
MODEL_NAME = "gemini-2.0-flash"  # 기본값
if os.getenv("VERTEX_PROJECT_ID"):
    MODEL_NAME = "Gemini 2.0 Flash"  # Vertex AI 연결 시

# nest_asyncio 적용: 이미 실행 중인 이벤트 루프 내에서 중첩 호출 허용
nest_asyncio.apply()

# 페이지 설정: 제목, 아이콘, 레이아웃 구성
st.set_page_config(page_title="스마트홈 에이전트", page_icon="🏠", layout="wide")

# 전역 이벤트 루프 생성 및 재사용
if "event_loop" not in st.session_state:
    loop = asyncio.new_event_loop()
    st.session_state.event_loop = loop
    asyncio.set_event_loop(loop)

# 스마트홈 그래프 초기화
if "smart_home_graph" not in st.session_state:
    st.session_state.smart_home_graph = create_smart_home_graph()

# 세션 상태 초기화
if "session_initialized" not in st.session_state:
    st.session_state.session_initialized = False
    st.session_state.history = []
    st.session_state.mcp_servers = {}
    st.session_state.mock_server_url = MOCK_SERVER_URL
    st.session_state.active_sidebar_tab = None

# 기본 MCP 설정
default_config = """{
  "weather": {
    "url": "http://localhost:3000/weather",
    "transport": "sse"
  }
}"""

# pending config가 없으면 기존 mcp_config_text 기반으로 생성
if "pending_mcp_config" not in st.session_state:
    try:
        st.session_state.pending_mcp_config = json.loads(
            st.session_state.get("mcp_config_text", default_config)
        )
    except Exception as e:
        st.error(f"초기 pending config 설정 실패: {e}")

# 타이틀 및 설명
st.title("🏠 스마트홈 에이전트")
st.markdown("✨ 스마트홈 가전제품 제어 및 루틴 관리를 위한 AI 에이전트입니다.")

# 사이드바 헤더
st.sidebar.markdown("### 🏠 스마트홈 에이전트")
st.sidebar.divider()

# MCP 서버 연결 테스트 함수
def test_mcp_connection(config):
    """MCP 서버 연결을 테스트합니다."""
    results = {}
    
    for tool_name, tool_config in config.items():
        try:
            # URL 기반 연결 테스트
            url = tool_config.get("url")
            if not url:
                results[tool_name] = {"status": "error", "message": "URL이 설정되지 않았습니다."}
                continue
                
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                results[tool_name] = {"status": "success", "message": "연결 성공"}
            else:
                results[tool_name] = {
                    "status": "error", 
                    "message": f"HTTP 오류: {response.status_code}", 
                    "detail": f"서버 응답 코드: {response.status_code}, 응답: {response.text[:200] if response.text else '내용 없음'}"
                }
        except requests.exceptions.ConnectionError as e:
            results[tool_name] = {
                "status": "error", 
                "message": "연결 오류: 서버에 연결할 수 없습니다", 
                "detail": str(e)
            }
        except requests.exceptions.Timeout as e:
            results[tool_name] = {
                "status": "error", 
                "message": "연결 오류: 연결 시간 초과", 
                "detail": str(e)
            }
        except Exception as e:
            results[tool_name] = {
                "status": "error", 
                "message": "연결 오류: 알 수 없는 오류", 
                "detail": str(e)
            }
    
    return results

# Mock 서버 연결 테스트 함수
def test_mock_server_connection(url):
    """Mock 서버 연결을 테스트합니다."""
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return {"status": "success", "message": "Mock 서버 연결 성공"}
        else:
            return {
                "status": "error", 
                "message": f"HTTP 오류: {response.status_code}", 
                "detail": f"서버 응답 코드: {response.status_code}, 응답: {response.text[:200] if response.text else '내용 없음'}"
            }
    except requests.exceptions.ConnectionError as e:
        return {
            "status": "error", 
            "message": "연결 오류: 서버에 연결할 수 없습니다", 
            "detail": str(e)
        }
    except requests.exceptions.Timeout as e:
        return {
            "status": "error", 
            "message": "연결 오류: 연결 시간 초과", 
            "detail": str(e)
        }
    except Exception as e:
        return {
            "status": "error", 
            "message": "연결 오류: 알 수 없는 오류", 
            "detail": str(e)
        }

# 시스템 정보
with st.sidebar:
    st.subheader("🔧 시스템 정보")
    st.write(f"🛠️ MCP 도구 수: {len(st.session_state.get('mcp_servers', {}))}")
    st.write(f"🏠 Mock 서버: {st.session_state.mock_server_url}")
    st.write(f"🧠 모델: {MODEL_NAME}")
    st.divider()

# Mock 서버 URL 설정
with st.sidebar:
    st.subheader("Mock 서버 설정")
    mock_server_url = st.text_input(
        "Mock 서버 URL", 
        value=st.session_state.mock_server_url
    )
    
    if mock_server_url != st.session_state.mock_server_url:
        st.session_state.mock_server_url = mock_server_url
        st.success(f"Mock 서버 URL이 {mock_server_url}로 설정되었습니다.")
        
    st.divider()

# MCP 도구 관리 - 사이드바에 확장 가능한 섹션으로 구현
with st.sidebar:
    st.subheader("🔌 MCP 도구 관리")
    
    # MCP 도구 추가 섹션
    with st.expander("MCP 도구 추가", expanded=st.session_state.active_sidebar_tab == "add"):
        st.markdown(
            """
        **하나의 도구**를 JSON 형식으로 입력하세요:
        
        ```json
        {
          "도구이름": {
            "url": "http://localhost:3000/도구경로",
            "transport": "sse"
          }
        }
        ```    
        ⚠️ **중요**: 현재는 transport "sse" 모드만 지원합니다.
        """
        )

        # 예시 JSON
        example_json = {
            "robot-cleaner": {
                "url": "http://0.0.0.0:8001/robot-cleaner/state",
                "transport": "sse",
            }
        }

        default_text = json.dumps(example_json, indent=2, ensure_ascii=False)

        new_tool_json = st.text_area(
            "도구 JSON",
            default_text,
            height=150,
        )

        # 추가하기 버튼
        if st.button(
            "도구 추가",
            type="primary",
            key="add_tool_button",
            use_container_width=True,
        ):
            try:
                # 입력값 검증
                if not new_tool_json.strip().startswith(
                    "{"
                ) or not new_tool_json.strip().endswith("}"):
                    st.error("JSON은 중괄호({})로 시작하고 끝나야 합니다.")
                else:
                    # JSON 파싱
                    parsed_tool = json.loads(new_tool_json)

                    # mcpServers 형식인지 확인하고 처리
                    if "mcpServers" in parsed_tool:
                        # mcpServers 안의 내용을 최상위로 이동
                        parsed_tool = parsed_tool["mcpServers"]
                        st.info("'mcpServers' 형식이 감지되었습니다. 자동으로 변환합니다.")

                    # 입력된 도구 수 확인
                    if len(parsed_tool) == 0:
                        st.error("최소 하나 이상의 도구를 입력해주세요.")
                    else:
                        # 모든 도구에 대해 처리
                        success_tools = []
                        for tool_name, tool_config in parsed_tool.items():
                            # URL 필드 확인
                            if "url" not in tool_config:
                                st.error(f"'{tool_name}' 도구에는 'url' 필드가 필요합니다.")
                                continue
                                
                            # transport 설정 (무조건 sse로 설정)
                            tool_config["transport"] = "sse"

                            # pending_mcp_config에 도구 추가
                            st.session_state.pending_mcp_config[tool_name] = tool_config
                            success_tools.append(tool_name)

                        # 성공 메시지
                        if success_tools:
                            if len(success_tools) == 1:
                                st.success(
                                    f"{success_tools[0]} 도구가 추가되었습니다. 적용하려면 '적용하기' 버튼을 눌러주세요."
                                )
                            else:
                                tool_names = ", ".join(success_tools)
                                st.success(
                                    f"총 {len(success_tools)}개 도구({tool_names})가 추가되었습니다. 적용하려면 '적용하기' 버튼을 눌러주세요."
                                )
                                
                            # 활성 탭 변경
                            st.session_state.active_sidebar_tab = "list"
                            st.rerun()
            except json.JSONDecodeError as e:
                st.error(f"JSON 파싱 에러: {e}")
                st.markdown(
                    f"""
                **수정 방법**:
                1. JSON 형식이 올바른지 확인하세요.
                2. 모든 키는 큰따옴표(")로 감싸야 합니다.
                3. 문자열 값도 큰따옴표(")로 감싸야 합니다.
                """
                )
            except Exception as e:
                st.error(f"오류 발생: {e}")
                
    # 등록된 도구 목록 섹션
    with st.expander("등록된 도구 목록", expanded=st.session_state.active_sidebar_tab == "list"):
        try:
            pending_config = st.session_state.pending_mcp_config
            
            if not pending_config:
                st.info("등록된 MCP 도구가 없습니다.")
            else:
                st.caption(f"등록된 MCP 도구 ({len(pending_config)}개)")
                # pending config의 키(도구 이름) 목록을 순회하며 표시
                for tool_name in list(pending_config.keys()):
                    col1, col2 = st.columns([7, 3])
                    col1.write(f"**{tool_name}**")
                    if col2.button("삭제", key=f"delete_{tool_name}", use_container_width=True):
                        # pending config에서 해당 도구 삭제 (즉시 적용되지는 않음)
                        del st.session_state.pending_mcp_config[tool_name]
                        st.success(
                            f"{tool_name} 도구가 삭제되었습니다."
                        )
                        st.rerun()
                
                # 도구 설정 세부 정보 표시
                st.caption("현재 도구 설정:")
                st.code(
                    json.dumps(st.session_state.pending_mcp_config, indent=2, ensure_ascii=False),
                    language="json"
                )
                
                # 적용하기 버튼
                if st.button(
                    "도구설정 적용하기",
                    key="apply_list_button",
                    type="primary",
                    use_container_width=True,
                ):
                    # 적용 중 메시지 표시
                    with st.spinner("변경사항을 적용하는 중..."):
                        # 설정 저장
                        st.session_state.mcp_config_text = json.dumps(
                            st.session_state.pending_mcp_config, indent=2, ensure_ascii=False
                        )
                        st.session_state.mcp_servers = st.session_state.pending_mcp_config.copy()
                        
                        # 진행 표시를 위한 지연
                        time.sleep(1)
                        
                        st.success("✅ 새로운 MCP 도구 설정이 적용되었습니다.")
                        st.info(f"🛠️ 총 {len(st.session_state.mcp_servers)}개의 MCP 도구가 로드되었습니다.")
                        
                        # 시스템 정보 갱신을 위해 재실행
                        time.sleep(1)
                        st.rerun()
        except Exception as e:
            st.error(f"유효한 MCP 도구 설정이 아닙니다: {str(e)}")
            
    # 연결 테스트 섹션
    with st.expander("연결 테스트", expanded=st.session_state.active_sidebar_tab == "test"):
        st.caption("서버 연결 테스트")
        
        # 테스트 버튼
        test_button = st.button("연결 테스트 실행", type="primary", use_container_width=True)
        
        # 결과 표시 영역을 상태와 상관없이 항상 생성하여 재실행 없이 토글되도록 합니다
        results_container = st.container()
        
        # 실패이유 상태 초기화
        if "error_details" not in st.session_state:
            st.session_state.error_details = {}
            
        if test_button:
            # 테스트 수행
            with st.spinner("서버 연결을 테스트하는 중..."):
                # Mock 서버 테스트
                mock_result = test_mock_server_connection(st.session_state.mock_server_url)
                
                # MCP 서버 테스트
                mcp_results = test_mcp_connection(st.session_state.pending_mcp_config)
                
                # 결과 저장
                st.session_state.mock_result = mock_result
                st.session_state.mcp_results = mcp_results
        
        # 테스트 결과가 있으면 표시
        if hasattr(st.session_state, 'mock_result') and hasattr(st.session_state, 'mcp_results'):
            with results_container:
                st.markdown("### 테스트 결과")
                
                # Mock 서버 결과
                mock_result = st.session_state.mock_result
                if mock_result["status"] == "success":
                    st.success(f"Mock 서버 : 연결 성공 ✅")
                else:
                    col1, col2 = st.columns([9, 3])
                    with col1:
                        st.error(f"Mock 서버 : 연결 실패 ❌")
                    with col2:
                        error_key = "mock_error_details"
                        if st.button("실패이유", key=error_key, use_container_width=True):
                            st.session_state.error_details[error_key] = not st.session_state.error_details.get(error_key, False)
                    
                    if st.session_state.error_details.get(error_key, False):
                        st.code(mock_result.get("detail", "상세 정보 없음"))
                        st.markdown("---")
                
                # MCP 서버 결과
                st.markdown("### MCP 도구 연결 결과")
                
                mcp_results = st.session_state.mcp_results
                if not mcp_results:
                    st.info("등록된 MCP 도구가 없습니다.")
                else:
                    for i, (tool_name, result) in enumerate(mcp_results.items()):
                        if result["status"] == "success":
                            st.success(f"{tool_name} : 연결 성공 ✅")
                        else:
                            col1, col2 = st.columns([9, 3])
                            with col1:
                                st.error(f"{tool_name} : 연결 실패 ❌")
                            with col2:
                                error_key = f"tool_error_{i}"
                                if st.button("실패이유", key=error_key, use_container_width=True):
                                    st.session_state.error_details[error_key] = not st.session_state.error_details.get(error_key, False)
                            
                            if st.session_state.error_details.get(error_key, False):
                                st.code(result.get("detail", "상세 정보 없음"))
                                st.markdown("---")
    
    st.divider()

# 대화 초기화 버튼
if st.sidebar.button("🔄 대화 초기화", use_container_width=True, type="primary"):
    # 대화 기록 초기화
    st.session_state.history = []
    st.sidebar.success("✅ 대화 기록이 초기화되었습니다.")
    st.rerun()

# 채팅 인터페이스
st.subheader("💬 대화")
st.markdown("스마트홈 가전제품을 제어하거나 루틴을 관리할 수 있습니다.")

# 대화 기록 출력
for message in st.session_state.get("history", []):
    if message["role"] == "user":
        st.chat_message("user").markdown(message["content"])
    elif message["role"] == "assistant":
        with st.chat_message("assistant"):
            st.markdown(message["content"])
            if "agent" in message:
                st.caption(f"응답: {message['agent']} 에이전트")

# 초기 실행 시 간단한 안내 메시지 표시
if not st.session_state.get("history"):
    st.info("""
    👋 안녕하세요! 스마트홈 멀티에이전트 시스템입니다.
    
    다음과 같은 기능을 제공합니다:
    - 📋 루틴 등록, 조회, 삭제, 제안
    - 🔌 가전제품(냉장고, 에어컨, 로봇청소기) 제어
    
    가전제품을 제어하는 예시:
    - "냉장고를 켜줘"
    - "에어컨 온도를 24도로 설정해줘"
    - "로봇청소기의 사용 가능한 모드를 알려줘"
    
    루틴을 관리하는 예시:
    - "현재 등록된 루틴 목록을 알려줘"
    - "취침 루틴을 만들어줘. 에어컨을 23도로 설정하고 로봇청소기를 꺼주는 루틴이야"
    """)

# 사용자 입력
user_query = st.chat_input("질문을 입력하세요")

if user_query:
    # 디버깅 메시지 컨테이너
    debug_container = st.sidebar.container()
    
    # 사용자 메시지 표시
    st.chat_message("user").markdown(user_query)
    
    # 대화 기록에 사용자 메시지 추가
    if "history" not in st.session_state:
        st.session_state.history = []
    st.session_state.history.append({"role": "user", "content": user_query})
    
    # 응답 생성
    with st.chat_message("assistant"):
        with st.spinner("응답 생성 중..."):
            try:
                # smart_home_graph 호출
                debug_container.info("멀티에이전트 그래프 호출 시작")
                start_time = time.time()
                
                # 그래프 호출
                result = st.session_state.smart_home_graph.invoke({
                    "messages": [HumanMessage(content=user_query)],
                    "next": None
                })
                
                elapsed_time = time.time() - start_time
                debug_container.success(f"그래프 응답 완료 (소요시간: {elapsed_time:.2f}초)")
                
                # 응답 추출
                if not result["messages"]:
                    st.error("에이전트 응답이 없습니다.")
                    response_text = "죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다."
                    agent_name = "unknown"
                else:
                    last_message = result["messages"][-1]
                    response_text = last_message.content
                    agent_name = getattr(last_message, "name", "unknown")
                    
                    debug_container.info(f"응답 에이전트: {agent_name}")
                
                # 응답 표시
                st.markdown(response_text)
                st.caption(f"응답: {agent_name} 에이전트")
                
                # 대화 기록에 어시스턴트 메시지 추가
                st.session_state.history.append({
                    "role": "assistant", 
                    "content": response_text,
                    "agent": agent_name
                })
                
            except Exception as e:
                st.error(f"오류가 발생했습니다: {str(e)}")
                debug_container.error(f"오류 발생: {str(e)}")
                import traceback
                debug_container.code(traceback.format_exc())
                
                # 오류 메시지를 대화 기록에 추가
                st.session_state.history.append({
                    "role": "assistant", 
                    "content": f"죄송합니다. 응답을 생성하는 중에 오류가 발생했습니다: {str(e)}",
                    "agent": "error"
                }) 