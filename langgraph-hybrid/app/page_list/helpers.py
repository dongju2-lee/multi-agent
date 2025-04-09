"""
페이지 상수 및 공통 유틸리티 함수
"""

import streamlit as st
import requests
from PIL import Image
import io
import os
import datetime
from logging_config import setup_logger

# 로거 설정
logger = setup_logger("helpers")

# 페이지 상수
HOME_PAGE = "홈"
CHATBOT_PAGE = "챗봇"
APPLIANCE_PAGE = "가전제품"
MOBILE_PAGE = "모바일"

# 모바일 서브페이지 상수
MESSAGES_SUBPAGE = "메시지"
PERSONALIZATION_SUBPAGE = "개인화 설정"
CALENDAR_SUBPAGE = "캘린더"

# 서버 URL
MOCK_SERVER_URL = "http://localhost:8000"

def format_timestamp(timestamp):
    """타임스탬프를 읽기 쉬운 형식으로 변환"""
    try:
        dt = datetime.datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception as e:
        logger.error(f"타임스탬프 변환 오류: {str(e)}")
        return "알 수 없는 시간"

def get_session_history(session_id):
    """지정된 세션 ID에 대한 대화 기록 가져오기"""
    try:
        from session_manager import SessionManager
        session_manager = SessionManager()
        history = session_manager.get_conversation_history(session_id)
        return history
    except Exception as e:
        logger.error(f"세션 기록 가져오기 실패: {str(e)}")
        st.error(f"대화 기록을 불러올 수 없습니다: {str(e)}")
        return []

def display_agent_graph(graph_type="full"):
    """에이전트 그래프 표시"""
    try:
        st.subheader("에이전트 그래프")
        
        graph_path = f"graphs/{graph_type}_graph.png"
        
        if os.path.exists(graph_path):
            image = Image.open(graph_path)
            st.image(image, use_column_width=True)
        else:
            st.warning(f"그래프 이미지를 찾을 수 없습니다: {graph_path}")
    except Exception as e:
        logger.error(f"에이전트 그래프 표시 오류: {str(e)}")
        st.error(f"에이전트 그래프를 표시할 수 없습니다: {str(e)}")

def display_mcp_servers_info():
    """MCP 서버 정보 표시"""
    try:
        st.subheader("MCP 서버 정보")
        
        # 서버 탭 생성
        tabs = st.tabs(["루틴", "인덕션", "냉장고", "전자레인지", "식품 매니저"])
        
        # 루틴 서버 정보
        with tabs[0]:
            try:
                response = requests.get(f"{MOCK_SERVER_URL}/routine/status", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    st.success("✅ 루틴 서버 연결됨")
                    st.json(data)
                    
                    # 루틴 툴 정보
                    if "tools" in data:
                        st.subheader("사용 가능한 툴")
                        for tool in data["tools"]:
                            with st.expander(f"{tool['name']}"):
                                st.write(f"**설명**: {tool.get('description', '설명 없음')}")
                                st.write(f"**파라미터**:")
                                for param, details in tool.get("parameters", {}).items():
                                    st.write(f"- {param}: {details.get('description', '설명 없음')}")
                else:
                    st.error(f"루틴 서버 응답 오류: {response.status_code}")
            except Exception as e:
                st.error(f"루틴 서버 연결 실패: {str(e)}")
        
        # 인덕션 서버 정보
        with tabs[1]:
            try:
                response = requests.get(f"{MOCK_SERVER_URL}/induction/status", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    st.success("✅ 인덕션 서버 연결됨")
                    st.json(data)
                else:
                    st.error(f"인덕션 서버 응답 오류: {response.status_code}")
            except Exception as e:
                st.error(f"인덕션 서버 연결 실패: {str(e)}")
        
        # 냉장고 서버 정보
        with tabs[2]:
            try:
                response = requests.get(f"{MOCK_SERVER_URL}/refrigerator/status", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    st.success("✅ 냉장고 서버 연결됨")
                    st.json(data)
                else:
                    st.error(f"냉장고 서버 응답 오류: {response.status_code}")
            except Exception as e:
                st.error(f"냉장고 서버 연결 실패: {str(e)}")
        
        # 전자레인지 서버 정보
        with tabs[3]:
            try:
                response = requests.get(f"{MOCK_SERVER_URL}/microwave/status", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    st.success("✅ 전자레인지 서버 연결됨")
                    st.json(data)
                else:
                    st.error(f"전자레인지 서버 응답 오류: {response.status_code}")
            except Exception as e:
                st.error(f"전자레인지 서버 연결 실패: {str(e)}")
        
        # 식품 매니저 서버 정보
        with tabs[4]:
            try:
                response = requests.get(f"{MOCK_SERVER_URL}/food_manager/status", timeout=2)
                if response.status_code == 200:
                    data = response.json()
                    st.success("✅ 식품 매니저 서버 연결됨")
                    st.json(data)
                else:
                    st.error(f"식품 매니저 서버 응답 오류: {response.status_code}")
            except Exception as e:
                st.error(f"식품 매니저 서버 연결 실패: {str(e)}")
                
    except Exception as e:
        logger.error(f"MCP 서버 정보 표시 오류: {str(e)}")
        st.error(f"MCP 서버 정보를 표시할 수 없습니다: {str(e)}") 