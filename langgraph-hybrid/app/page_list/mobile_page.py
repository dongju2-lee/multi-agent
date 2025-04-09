import streamlit as st
import requests
from logging_config import setup_logger

# 로거 설정
logger = setup_logger("mobile_page")

# 모의 서버 URL
MOCK_SERVER_URL = "http://localhost:8000"

# 모바일 서브페이지 상수
MESSAGE_PAGE = "messages"
PERSONALIZATION_PAGE = "personalization"
CALENDAR_PAGE = "calendar"

def get_user_personalization():
    """
    사용자 개인화 정보를 가져옵니다.
    """
    try:
        response = requests.get(f"{MOCK_SERVER_URL}/user/personalization", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"개인화 정보 조회 실패: {response.status_code}")
            return {"result": "fail", "user_personalization_info": []}
    except requests.exceptions.RequestException as e:
        logger.error(f"개인화 정보 조회 실패: {str(e)}")
        return {"result": "fail", "user_personalization_info": [], "error": str(e)}

def get_user_calendar():
    """
    사용자 캘린더 정보를 가져옵니다.
    """
    try:
        response = requests.get(f"{MOCK_SERVER_URL}/user/calendar", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"캘린더 정보 조회 실패: {response.status_code}")
            return {"result": "fail", "calendar_info": None}
    except requests.exceptions.RequestException as e:
        logger.error(f"캘린더 정보 조회 실패: {str(e)}")
        return {"result": "fail", "calendar_info": None, "error": str(e)}

def get_user_messages():
    """
    사용자 메시지 목록을 가져옵니다.
    """
    try:
        response = requests.get(f"{MOCK_SERVER_URL}/user/message", timeout=5)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"메시지 목록 조회 실패: {response.status_code}")
            return {"result": "fail", "messages": []}
    except requests.exceptions.RequestException as e:
        logger.error(f"메시지 목록 조회 실패: {str(e)}")
        return {"result": "fail", "messages": [], "error": str(e)}

def mobile_page():
    """
    모바일 앱 연동 페이지입니다.
    """
    st.title("📱 모바일 앱 연동")
    st.markdown("---")
    
    # 페이지 설명
    st.markdown("""
    스마트홈 시스템의 모바일 앱과 연동된 정보를 확인하고 관리할 수 있는 페이지입니다.
    사용자 메시지, 개인화 정보, 캘린더 등의 정보를 확인하고 업데이트할 수 있습니다.
    """)
    
    # 서브페이지 네비게이션
    if "mobile_subpage" not in st.session_state:
        st.session_state.mobile_subpage = MESSAGE_PAGE
    
    # 서브페이지 선택 도구
    selected_page = st.selectbox(
        "보기:",
        [MESSAGE_PAGE, PERSONALIZATION_PAGE, CALENDAR_PAGE],
        format_func=lambda x: {
            MESSAGE_PAGE: "📬 메시지",
            PERSONALIZATION_PAGE: "👤 개인화 정보",
            CALENDAR_PAGE: "📅 캘린더"
        }.get(x, x),
        index=[MESSAGE_PAGE, PERSONALIZATION_PAGE, CALENDAR_PAGE].index(st.session_state.mobile_subpage)
    )
    
    # 서브페이지 상태 업데이트
    st.session_state.mobile_subpage = selected_page
    
    # 새로고침 버튼
    if st.button("🔄 새로고침"):
        st.experimental_rerun()
    
    st.markdown("---")
    
    # 메시지 페이지
    if selected_page == MESSAGE_PAGE:
        st.header("📬 메시지")
        
        # 메시지 데이터 가져오기
        with st.spinner("메시지 로딩 중..."):
            message_data = get_user_messages()
        
        if message_data.get("result", "") == "fail":
            if "error" in message_data:
                st.error(f"메시지를 가져오는 중 오류가 발생했습니다: {message_data['error']}")
            else:
                st.error("메시지를 가져오는 중 오류가 발생했습니다.")
        else:
            messages = message_data.get("messages", [])
            
            if not messages:
                st.info("📭 수신된 메시지가 없습니다.")
            else:
                for msg in messages:
                    with st.expander(f"**{msg.get('message_name', '알 수 없는 메시지')}** - {msg.get('data', '')}"):
                        st.write(msg.get("message_body", "내용 없음"))
    
    # 개인화 정보 페이지
    elif selected_page == PERSONALIZATION_PAGE:
        st.header("👤 개인화 정보")
        
        # 개인화 정보 가져오기
        with st.spinner("개인화 정보 로딩 중..."):
            personalization_data = get_user_personalization()
        
        if personalization_data.get("result", "") == "fail":
            if "error" in personalization_data:
                st.error(f"개인화 정보를 가져오는 중 오류가 발생했습니다: {personalization_data['error']}")
            else:
                st.error("개인화 정보를 가져오는 중 오류가 발생했습니다.")
        else:
            personalization_info = personalization_data.get("user_personalization_info", [])
            
            # 개인화 정보 표시
            if not personalization_info:
                st.info("저장된 개인화 정보가 없습니다.")
            else:
                st.markdown("### 저장된 정보")
                for i, info in enumerate(personalization_info, 1):
                    st.info(f"{i}. {info}")
            
            # 새 개인화 정보 추가 폼
            st.markdown("### 새 개인화 정보 추가")
            with st.form("add_personalization_form"):
                new_info = st.text_area("정보 입력", placeholder="예: 좋아하는 음식은 치킨입니다.")
                submit_button = st.form_submit_button("저장")
                
                if submit_button and new_info:
                    try:
                        response = requests.post(
                            f"{MOCK_SERVER_URL}/user/personalization",
                            json={"info": new_info},
                            timeout=5
                        )
                        
                        if response.status_code == 200:
                            st.success("✅ 개인화 정보가 저장되었습니다.")
                            st.experimental_rerun()
                        else:
                            st.error(f"❌ 저장 실패: {response.status_code}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"❌ 저장 실패: {str(e)}")
    
    # 캘린더 페이지
    elif selected_page == CALENDAR_PAGE:
        st.header("📅 캘린더")
        
        # 캘린더 정보 가져오기
        with st.spinner("캘린더 정보 로딩 중..."):
            calendar_data = get_user_calendar()
        
        if calendar_data.get("result", "") == "fail":
            if "error" in calendar_data:
                st.error(f"캘린더 정보를 가져오는 중 오류가 발생했습니다: {calendar_data['error']}")
            else:
                st.error("캘린더 정보를 가져오는 중 오류가 발생했습니다.")
        else:
            calendar_info = calendar_data.get("calendar_info", {})
            
            if not calendar_info:
                st.info("캘린더 정보가 없습니다.")
            else:
                month = calendar_info.get("month", 0)
                st.markdown(f"### {month}월 일정")
                
                info_of_day = calendar_info.get("info_of_day", {})
                
                if not info_of_day:
                    st.info("일정이 없습니다.")
                else:
                    for day, events in info_of_day.items():
                        st.markdown(f"#### {day}")
                        if not events:
                            st.write("일정이 없습니다.")
                        else:
                            for event in events:
                                st.info(f"**{event.get('time', '시간 미정')}** - {event.get('info', '상세 정보 없음')}")
            
            # 새 일정 추가 폼
            st.markdown("### 새 일정 추가")
            with st.form("add_calendar_form"):
                day = st.text_input("날짜", placeholder="예: day15")
                time = st.text_input("시간", placeholder="예: 14:00")
                event_info = st.text_area("일정 내용", placeholder="예: 가족 식사")
                
                submit_button = st.form_submit_button("일정 추가")
                
                if submit_button and day and time and event_info:
                    try:
                        response = requests.post(
                            f"{MOCK_SERVER_URL}/user/calendar",
                            json={
                                "day": day,
                                "time": time,
                                "info": event_info
                            },
                            timeout=5
                        )
                        
                        if response.status_code == 200:
                            st.success("✅ 일정이 추가되었습니다.")
                            st.experimental_rerun()
                        else:
                            st.error(f"❌ 저장 실패: {response.status_code}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"❌ 저장 실패: {str(e)}")
    
    logger.info(f"모바일 페이지가 로드되었습니다. (서브페이지: {selected_page})") 