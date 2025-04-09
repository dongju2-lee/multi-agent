import streamlit as st
import requests
import time
from logging_config import setup_logger

# 로거 설정
logger = setup_logger("appliance_page")

# 모의 서버 URL
MOCK_SERVER_URL = "http://localhost:8000"

def get_refrigerator_display():
    """냉장고 디스플레이 정보 가져오기"""
    try:
        response = requests.get(f"{MOCK_SERVER_URL}/refrigerator/cooking-state", timeout=2)
        if response.status_code == 200:
            data = response.json()
            return f"🟢 요리 상태: {data['cooking_state']}"
        else:
            return f"🔴 오류 발생: 서버 응답 코드 {response.status_code}"
    except Exception as e:
        logger.error(f"냉장고 상태 확인 오류: {str(e)}")
        return f"🔴 연결 오류: {str(e)}"

def get_induction_state():
    """인덕션 상태 가져오기"""
    try:
        response = requests.get(f"{MOCK_SERVER_URL}/Induction/power/state", timeout=2)
        if response.status_code == 200:
            data = response.json()
            power_state = data.get("power_state", "알 수 없음")
            
            # 전원 상태에 따라 진행 표시줄 설정
            if power_state == "on":
                st.success("전원이 켜져 있습니다")
                st.progress(100)
                return "🟢 전원 켜짐"
            else:
                st.error("전원이 꺼져 있습니다")
                st.progress(0)
                return "🔴 전원 꺼짐"
        else:
            return f"🔴 오류 발생: 서버 응답 코드 {response.status_code}"
    except Exception as e:
        logger.error(f"인덕션 상태 확인 오류: {str(e)}")
        return f"🔴 연결 오류: {str(e)}"

def get_microwave_state():
    """전자레인지 상태 가져오기"""
    try:
        # 전원 상태 조회
        power_response = requests.get(f"{MOCK_SERVER_URL}/microwave/power/state", timeout=2)
        # 모드 조회
        mode_response = requests.get(f"{MOCK_SERVER_URL}/microwave/mode", timeout=2)
        
        if power_response.status_code == 200 and mode_response.status_code == 200:
            power_data = power_response.json()
            mode_data = mode_response.json()
            
            power_state = power_data.get("power_state", "알 수 없음")
            current_mode = mode_data.get("mode", "알 수 없음")
            
            # 전원 상태에 따라 진행 표시줄 설정
            if power_state == "on":
                st.success(f"전원이 켜져 있습니다 (모드: {current_mode})")
                st.progress(100)
                return f"🟢 전원 켜짐 (모드: {current_mode})"
            else:
                st.error("전원이 꺼져 있습니다")
                st.progress(0)
                return "🔴 전원 꺼짐"
        else:
            error_code = power_response.status_code if power_response.status_code != 200 else mode_response.status_code
            return f"🔴 오류 발생: 서버 응답 코드 {error_code}"
    except Exception as e:
        logger.error(f"전자레인지 상태 확인 오류: {str(e)}")
        return f"🔴 연결 오류: {str(e)}"

def appliance_page():
    """가전제품 상태 페이지 표시"""
    st.title("🔌 가전제품 상태")
    st.markdown("---")
    
    st.markdown("""
    가전제품의 현재 상태를 확인할 수 있는 페이지입니다.
    """)
    
    # 수동 새로고침 버튼
    if st.button("🔄 수동 새로고침"):
        st.experimental_rerun()
    
    # 냉장고, 인덕션, 전자레인지 상태를 3개 열로 표시
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("냉장고")
        refrigerator_state = get_refrigerator_display()
        st.markdown(f"### {refrigerator_state}")
    
    with col2:
        st.subheader("인덕션")
        induction_state = get_induction_state()
        st.markdown(f"### {induction_state}")
    
    with col3:
        st.subheader("전자레인지")
        microwave_state = get_microwave_state()
        st.markdown(f"### {microwave_state}")
    
    logger.info("가전제품 페이지가 로드되었습니다.") 