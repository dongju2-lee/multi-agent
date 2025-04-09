"""
스마트홈 매니저 홈 페이지
"""

import streamlit as st
from PIL import Image
import os
import base64
from logging_config import setup_logger

# 로거 설정
logger = setup_logger("home_page")

def get_image_base64(image_path):
    """이미지 파일을 Base64 인코딩으로 변환"""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        st.error(f"이미지 로드 실패: {str(e)}")
        return None

def home_page():
    """홈 페이지 렌더링"""
    st.title("🏠 스마트홈 매니저에 오신 것을 환영합니다")
    
    st.markdown("""
    ## 스마트홈 매니저란?
    
    스마트홈 매니저는 다중 에이전트 시스템을 활용하여 가정 내 다양한 스마트 기기들을 
    효율적으로 관리하고 제어할 수 있는 통합 플랫폼입니다.
    
    ### 주요 기능
    
    이 애플리케이션은 다음과 같은 주요 기능을 제공합니다:
    """)
    
    # 주요 기능 설명을 열 형태로 표시
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        #### 💬 챗봇 인터페이스
        
        자연어로 스마트홈 기기와 대화하고 
        명령을 내릴 수 있습니다. 다중 에이전트 
        시스템이 복잡한 요청도 처리합니다.
        """)
    
    with col2:
        st.markdown("""
        #### 🔌 가전제품 상태 모니터링
        
        냉장고, 인덕션, 전자레인지 등 
        가전제품의 상태를 실시간으로 
        확인하고 제어할 수 있습니다.
        """)
    
    with col3:
        st.markdown("""
        #### 📱 모바일 기기 연동
        
        사용자의 모바일 기기와 연동하여
        메시지, 개인 설정, 캘린더 정보를
        확인하고 관리할 수 있습니다.
        """)
    
    st.markdown("---")
    
    # 시스템 아키텍처 설명
    st.header("시스템 아키텍처")
    
    st.markdown("""
    스마트홈 매니저는 LangGraph 기반의 멀티 에이전트 시스템을 사용하여 
    다양한 기기 간의 조율된 통신을 가능하게 합니다.
    
    - **루틴 에이전트**: 일상적인 작업 및 자동화 시나리오를 관리
    - **기기별 에이전트**: 각 스마트 기기의 제어 및 상태 관리
    - **식품 매니저 에이전트**: 냉장고 내용물 및 식품 관리
    - **모바일 연동 에이전트**: 모바일 기기와의 연동 및 알림 관리
    """)
    
    st.markdown("---")
    
    # 사용 방법 안내
    st.header("사용 방법")
    
    st.markdown("""
    1. **페이지 선택**: 사이드바에서 원하는 페이지를 선택합니다
    2. **기능 사용**: 각 페이지에서 제공하는 기능을 활용합니다
    
    ### 페이지 안내
    
    - **홈**: 시스템 개요 및 사용 방법 안내 (현재 페이지)
    - **챗봇**: 자연어로 스마트홈 시스템과 대화
    - **가전제품**: 가전제품 상태 모니터링 및 제어
    - **모바일**: 모바일 기기 연동 정보 확인 및 관리
    """)
    
    # 바로가기 버튼
    st.markdown("---")
    st.header("바로가기")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("### 💬 챗봇")
        st.markdown("자연어로 스마트홈과 대화하고 제어하세요.")
    
    with col2:
        st.markdown("### 🔌 가전제품")
        st.markdown("가전제품의 상태를 확인하고 모니터링하세요.")
    
    with col3:
        st.markdown("### 📱 모바일")
        st.markdown("모바일 연동 정보를 확인하고 관리하세요.")
    
    logger.info("홈 페이지가 로드되었습니다.") 