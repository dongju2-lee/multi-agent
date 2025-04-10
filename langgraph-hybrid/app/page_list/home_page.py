"""
스마트홈 매니저 홈 페이지
"""

import streamlit as st
import os
from datetime import datetime
from logging_config import setup_logger
from page_list.helpers import CHATBOT_PAGE, APPLIANCE_PAGE, MOBILE_PAGE

# 로거 설정
logger = setup_logger("home_page")

def home_page():
    """
    스마트홈 관리 시스템 메인 페이지입니다.
    """
    st.title("🏠 스마트홈 매니저 홈")
    st.markdown("---")
    
    # 시스템 소개
    st.header("시스템 소개")
    st.markdown("""
    **스마트홈 매니저**는 자연어 기반 멀티에이전트 시스템으로, 가전제품 제어와 관리를 도와드립니다.
    
    각 에이전트가 자신의 전문 영역에서 협업하여 사용자의 요청을 처리합니다:
    
    - **슈퍼바이저 에이전트**: 사용자 의도를 이해하고 적절한 전문 에이전트에게 작업을 분배합니다.
    - **가전 에이전트**: 인덕션, 냉장고, 전자레인지 등의 가전제품을 제어합니다.
    - **식품 관리 에이전트**: 냉장고 내 식품 정보와 레시피를 관리합니다.
    - **루틴 에이전트**: 반복적인 작업을 자동화하는 루틴을 관리합니다.
    """)
    
    # 주요 기능
    st.header("주요 기능")
    
    # 대화형 인터페이스 기능 소개
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("💬 대화형 인터페이스")
        st.markdown("""
        - 자연어로 가전제품 제어
        - 멀티에이전트 시스템이 복잡한 요청 처리
        - 대화 기록 저장 및 불러오기
        """)
        st.button("👉 챗봇으로 이동", use_container_width=True, 
                 help="자연어로 가전제품을 제어하는 챗봇 페이지로 이동합니다.",
                 on_click=lambda: st.switch_page(CHATBOT_PAGE) if hasattr(st, 'switch_page') else None)
    
    with col2:
        st.subheader("🧠 스마트 가전 관리")
        st.markdown("""
        - 가전제품 상태 모니터링
        - 원격 제어 및 설정 변경
        - 실시간 상태 업데이트
        """)
        st.button("👉 가전제품으로 이동", use_container_width=True,
                 help="가전제품 상태를 확인하고 제어하는 페이지로 이동합니다.",
                 on_click=lambda: st.switch_page(APPLIANCE_PAGE) if hasattr(st, 'switch_page') else None)
    
    with col3:
        st.subheader("📱 모바일 연동")
        st.markdown("""
        - 모바일 디바이스 상태 확인
        - 알림 및 메시지 관리
        - 일정 및 개인화 설정
        """)
        st.button("👉 모바일로 이동", use_container_width=True,
                 help="모바일 연동 정보를 확인하는 페이지로 이동합니다.",
                 on_click=lambda: st.switch_page(MOBILE_PAGE) if hasattr(st, 'switch_page') else None)
    
    # 시스템 정보 표시
    st.markdown("---")
    st.header("시스템 정보")
    
    # 현재 시간 표시
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.info(f"현재 시간: {current_time}")
    
    # Python 및 패키지 버전 정보
    with st.expander("시스템 버전 정보"):
        st.markdown("""
        - **Python**: 3.10.0
        - **Streamlit**: 1.31.0
        - **LangChain**: 0.3.0
        - **LangGraph**: 0.3.0
        - **Google Vertex AI**: 2.0.0
        """)
    
    logger.info("홈 페이지가 로드되었습니다.") 