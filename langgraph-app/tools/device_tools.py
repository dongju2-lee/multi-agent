import os
import json
import requests
import traceback
from typing import List, Dict, Annotated
from dotenv import load_dotenv
from langchain_core.tools import tool
from logging_config import setup_logger

# 로거 설정
logger = setup_logger("device_tools")

# 환경 변수 로드
load_dotenv()
MOCK_SERVER_URL = os.getenv("MOCK_SERVER_URL", "http://localhost:8000")

# --------- 냉장고 도구 ---------
class RefrigeratorTools:
    @tool
    def get_refrigerator_state():
        """냉장고의 현재 상태(켜짐/꺼짐)를 조회합니다."""
        logger.info("냉장고 상태 조회 도구 호출됨")
        url = f"{MOCK_SERVER_URL}/refrigerator/state"
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            logger.info(f"냉장고 상태 조회 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"냉장고 상태 조회 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}
    
    @tool
    def set_refrigerator_state(state: Annotated[str, "냉장고 상태 (on 또는 off)"]):
        """냉장고의 상태를 설정합니다. 'on' 또는 'off'로 지정합니다."""
        logger.info(f"냉장고 상태 설정 도구 호출됨: {state}")
        url = f"{MOCK_SERVER_URL}/refrigerator/state"
        payload = {"state": state}
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info(f"냉장고 상태 설정 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"냉장고 상태 설정 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}
    
    @tool
    def get_refrigerator_mode():
        """냉장고의 현재 모드를 조회합니다."""
        logger.info("냉장고 모드 조회 도구 호출됨")
        url = f"{MOCK_SERVER_URL}/refrigerator/mode"
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            logger.info(f"냉장고 모드 조회 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"냉장고 모드 조회 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}
    
    @tool
    def set_refrigerator_mode(mode: Annotated[str, "냉장고 모드"]):
        """냉장고의 모드를 설정합니다."""
        logger.info(f"냉장고 모드 설정 도구 호출됨: {mode}")
        url = f"{MOCK_SERVER_URL}/refrigerator/mode"
        payload = {"mode": mode}
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info(f"냉장고 모드 설정 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"냉장고 모드 설정 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}
    
    @tool
    def get_refrigerator_mode_list():
        """냉장고에서 사용 가능한 모드 목록을 조회합니다."""
        logger.info("냉장고 모드 목록 조회 도구 호출됨")
        url = f"{MOCK_SERVER_URL}/refrigerator/mode/list"
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            logger.info(f"냉장고 모드 목록 조회 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"냉장고 모드 목록 조회 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}
    
    @tool
    def get_refrigerator_food_list():
        """냉장고에 보관 중인 식품 목록을 조회합니다."""
        logger.info("냉장고 식품 목록 조회 도구 호출됨")
        url = f"{MOCK_SERVER_URL}/refrigerator/food"
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            logger.info(f"냉장고 식품 목록 조회 결과: {len(result.get('foods', []))}개 식품 확인됨")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"냉장고 식품 목록 조회 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}

# --------- 에어컨 도구 ---------
class AirConditionerTools:
    @tool
    def get_air_conditioner_state():
        """에어컨의 현재 상태(켜짐/꺼짐)를 조회합니다."""
        logger.info("에어컨 상태 조회 도구 호출됨")
        url = f"{MOCK_SERVER_URL}/air-conditioner/state"
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            logger.info(f"에어컨 상태 조회 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"에어컨 상태 조회 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}
    
    @tool
    def set_air_conditioner_state(state: Annotated[str, "에어컨 상태 (on 또는 off)"]):
        """에어컨의 상태를 설정합니다. 'on' 또는 'off'로 지정합니다."""
        logger.info(f"에어컨 상태 설정 도구 호출됨: {state}")
        url = f"{MOCK_SERVER_URL}/air-conditioner/state"
        payload = {"state": state}
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info(f"에어컨 상태 설정 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"에어컨 상태 설정 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}
    
    @tool
    def get_air_conditioner_mode():
        """에어컨의 현재 모드를 조회합니다."""
        logger.info("에어컨 모드 조회 도구 호출됨")
        url = f"{MOCK_SERVER_URL}/air-conditioner/mode"
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            logger.info(f"에어컨 모드 조회 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"에어컨 모드 조회 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}
    
    @tool
    def set_air_conditioner_mode(mode: Annotated[str, "에어컨 모드"]):
        """에어컨의 모드를 설정합니다."""
        logger.info(f"에어컨 모드 설정 도구 호출됨: {mode}")
        url = f"{MOCK_SERVER_URL}/air-conditioner/mode"
        payload = {"mode": mode}
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info(f"에어컨 모드 설정 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"에어컨 모드 설정 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}
    
    @tool
    def get_air_conditioner_mode_list():
        """에어컨에서 사용 가능한 모드 목록을 조회합니다."""
        logger.info("에어컨 모드 목록 조회 도구 호출됨")
        url = f"{MOCK_SERVER_URL}/air-conditioner/mode/list"
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            logger.info(f"에어컨 모드 목록 조회 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"에어컨 모드 목록 조회 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}
    
    @tool
    def get_air_conditioner_filter_usage():
        """에어컨 필터 사용량을 조회합니다."""
        logger.info("에어컨 필터 사용량 조회 도구 호출됨")
        url = f"{MOCK_SERVER_URL}/air-conditioner/filter"
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            logger.info(f"에어컨 필터 사용량 조회 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"에어컨 필터 사용량 조회 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}
    
    @tool
    def get_air_conditioner_temperature():
        """에어컨의 현재 설정 온도를 조회합니다."""
        logger.info("에어컨 온도 조회 도구 호출됨")
        url = f"{MOCK_SERVER_URL}/air-conditioner/temperature"
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            logger.info(f"에어컨 온도 조회 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"에어컨 온도 조회 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}
    
    @tool
    def set_air_conditioner_temperature(temperature: Annotated[int, "설정할 온도"]):
        """에어컨의 온도를 설정합니다."""
        logger.info(f"에어컨 온도 설정 도구 호출됨: {temperature}도")
        url = f"{MOCK_SERVER_URL}/air-conditioner/temperature"
        payload = {"temperature": temperature}
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info(f"에어컨 온도 설정 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"에어컨 온도 설정 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}
    
    @tool
    def increase_air_conditioner_temperature():
        """에어컨 온도를 1도 올립니다."""
        logger.info("에어컨 온도 증가 도구 호출됨")
        url = f"{MOCK_SERVER_URL}/air-conditioner/temperature/increase"
        try:
            response = requests.post(url)
            response.raise_for_status()
            result = response.json()
            logger.info(f"에어컨 온도 증가 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"에어컨 온도 증가 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}
    
    @tool
    def decrease_air_conditioner_temperature():
        """에어컨 온도를 1도 내립니다."""
        logger.info("에어컨 온도 감소 도구 호출됨")
        url = f"{MOCK_SERVER_URL}/air-conditioner/temperature/decrease"
        try:
            response = requests.post(url)
            response.raise_for_status()
            result = response.json()
            logger.info(f"에어컨 온도 감소 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"에어컨 온도 감소 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}
    
    @tool
    def get_air_conditioner_temperature_range():
        """에어컨의 설정 가능한 온도 범위를 조회합니다."""
        logger.info("에어컨 온도 범위 조회 도구 호출됨")
        url = f"{MOCK_SERVER_URL}/air-conditioner/temperature/range"
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            logger.info(f"에어컨 온도 범위 조회 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"에어컨 온도 범위 조회 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}

# --------- 로봇청소기 도구 ---------
class RobotCleanerTools:
    @tool
    def get_robot_cleaner_state():
        """로봇청소기의 현재 상태(켜짐/꺼짐)를 조회합니다."""
        logger.info("로봇청소기 상태 조회 도구 호출됨")
        url = f"{MOCK_SERVER_URL}/robot-cleaner/state"
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            logger.info(f"로봇청소기 상태 조회 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"로봇청소기 상태 조회 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}
    
    @tool
    def set_robot_cleaner_state(state: Annotated[str, "로봇청소기 상태 (on 또는 off)"]):
        """로봇청소기의 상태를 설정합니다. 'on' 또는 'off'로 지정합니다."""
        logger.info(f"로봇청소기 상태 설정 도구 호출됨: {state}")
        url = f"{MOCK_SERVER_URL}/robot-cleaner/state"
        payload = {"state": state}
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info(f"로봇청소기 상태 설정 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"로봇청소기 상태 설정 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}
    
    @tool
    def get_robot_cleaner_mode():
        """로봇청소기의 현재 모드를 조회합니다."""
        logger.info("로봇청소기 모드 조회 도구 호출됨")
        url = f"{MOCK_SERVER_URL}/robot-cleaner/mode"
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            logger.info(f"로봇청소기 모드 조회 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"로봇청소기 모드 조회 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}
    
    @tool
    def set_robot_cleaner_mode(mode: Annotated[str, "로봇청소기 모드"]):
        """로봇청소기의 모드를 설정합니다."""
        logger.info(f"로봇청소기 모드 설정 도구 호출됨: {mode}")
        url = f"{MOCK_SERVER_URL}/robot-cleaner/mode"
        payload = {"mode": mode}
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info(f"로봇청소기 모드 설정 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"로봇청소기 모드 설정 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}
    
    @tool
    def get_robot_cleaner_mode_list():
        """로봇청소기에서 사용 가능한 모드 목록을 조회합니다."""
        logger.info("로봇청소기 모드 목록 조회 도구 호출됨")
        url = f"{MOCK_SERVER_URL}/robot-cleaner/mode/list"
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            logger.info(f"로봇청소기 모드 목록 조회 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"로봇청소기 모드 목록 조회 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}
    
    @tool
    def get_robot_cleaner_filter_usage():
        """로봇청소기 필터 사용량을 조회합니다."""
        logger.info("로봇청소기 필터 사용량 조회 도구 호출됨")
        url = f"{MOCK_SERVER_URL}/robot-cleaner/filter"
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            logger.info(f"로봇청소기 필터 사용량 조회 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"로봇청소기 필터 사용량 조회 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}
    
    @tool
    def get_robot_cleaner_count():
        """로봇청소기의 청소 횟수를 조회합니다."""
        logger.info("로봇청소기 청소 횟수 조회 도구 호출됨")
        url = f"{MOCK_SERVER_URL}/robot-cleaner/cleaner-count"
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            logger.info(f"로봇청소기 청소 횟수 조회 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"로봇청소기 청소 횟수 조회 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}
    
    @tool
    def get_available_patrol_areas():
        """로봇청소기의 방범 가능한 구역 목록을 조회합니다."""
        logger.info("로봇청소기 방범 가능 구역 목록 조회 도구 호출됨")
        url = f"{MOCK_SERVER_URL}/robot-cleaner/patrol/list"
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            logger.info(f"로봇청소기 방범 가능 구역 목록 조회 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"로봇청소기 방범 가능 구역 목록 조회 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}
    
    @tool
    def get_patrol_settings():
        """로봇청소기의 현재 방범 구역 설정을 조회합니다."""
        logger.info("로봇청소기 방범 구역 설정 조회 도구 호출됨")
        url = f"{MOCK_SERVER_URL}/robot-cleaner/patrol/setting"
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            logger.info(f"로봇청소기 방범 구역 설정 조회 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"로봇청소기 방범 구역 설정 조회 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}
    
    @tool
    def set_patrol_areas(areas: Annotated[List[str], "설정할 방범 구역 목록"]):
        """로봇청소기의 방범 구역을 설정하고 방범 모드를 시작합니다."""
        logger.info(f"로봇청소기 방범 구역 설정 도구 호출됨: {areas}")
        url = f"{MOCK_SERVER_URL}/robot-cleaner/patrol/start"
        try:
            response = requests.post(url, json={"areas": areas})
            response.raise_for_status()
            result = response.json()
            logger.info(f"로봇청소기 방범 구역 설정 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"로봇청소기 방범 구역 설정 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}

# --------- 도구 목록 반환 함수 ---------
def get_refrigerator_tools():
    """냉장고 관련 도구 목록을 반환합니다."""
    logger.info("냉장고 도구 목록 로드됨")
    return [
        RefrigeratorTools.get_refrigerator_state,
        RefrigeratorTools.set_refrigerator_state,
        RefrigeratorTools.get_refrigerator_mode,
        RefrigeratorTools.set_refrigerator_mode,
        RefrigeratorTools.get_refrigerator_mode_list,
        RefrigeratorTools.get_refrigerator_food_list,
    ]

def get_air_conditioner_tools():
    """에어컨 관련 도구 목록을 반환합니다."""
    logger.info("에어컨 도구 목록 로드됨")
    return [
        AirConditionerTools.get_air_conditioner_state,
        AirConditionerTools.set_air_conditioner_state,
        AirConditionerTools.get_air_conditioner_mode,
        AirConditionerTools.set_air_conditioner_mode,
        AirConditionerTools.get_air_conditioner_mode_list,
        AirConditionerTools.get_air_conditioner_filter_usage,
        AirConditionerTools.get_air_conditioner_temperature,
        AirConditionerTools.set_air_conditioner_temperature,
        AirConditionerTools.increase_air_conditioner_temperature,
        AirConditionerTools.decrease_air_conditioner_temperature,
        AirConditionerTools.get_air_conditioner_temperature_range,
    ]

def get_robot_cleaner_tools():
    """로봇청소기 관련 도구 목록을 반환합니다."""
    logger.info("로봇청소기 도구 목록 로드됨")
    return [
        RobotCleanerTools.get_robot_cleaner_state,
        RobotCleanerTools.set_robot_cleaner_state,
        RobotCleanerTools.get_robot_cleaner_mode,
        RobotCleanerTools.set_robot_cleaner_mode,
        RobotCleanerTools.get_robot_cleaner_mode_list,
        RobotCleanerTools.get_robot_cleaner_filter_usage,
        RobotCleanerTools.get_robot_cleaner_count,
        RobotCleanerTools.get_available_patrol_areas,
        RobotCleanerTools.get_patrol_settings,
        RobotCleanerTools.set_patrol_areas,
    ]

def get_all_device_tools():
    """모든 가전제품 제어 도구 목록을 반환합니다."""
    logger.info("모든 가전제품 도구 목록 로드됨")
    all_tools = []
    all_tools.extend(get_refrigerator_tools())
    all_tools.extend(get_air_conditioner_tools())
    all_tools.extend(get_robot_cleaner_tools())
    return all_tools 