import os
import json
import requests
import traceback
from typing import List, Dict, Annotated
from dotenv import load_dotenv
from langchain_core.tools import tool
from logging_config import setup_logger

# 로거 설정
logger = setup_logger("robot_cleaner_tools")

# 환경 변수 로드
load_dotenv()
MOCK_SERVER_URL = os.getenv("MOCK_SERVER_URL")

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
    def get_robot_cleaner_battery():
        """로봇청소기의 현재 배터리 잔량을 조회합니다."""
        logger.info("로봇청소기 배터리 조회 도구 호출됨")
        url = f"{MOCK_SERVER_URL}/robot-cleaner/battery"
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            logger.info(f"로봇청소기 배터리 조회 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"로봇청소기 배터리 조회 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}
    
    @tool
    def get_robot_cleaner_area():
        """로봇청소기가 현재 청소하고 있는 구역을 조회합니다."""
        logger.info("로봇청소기 청소 구역 조회 도구 호출됨")
        url = f"{MOCK_SERVER_URL}/robot-cleaner/area"
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            logger.info(f"로봇청소기 청소 구역 조회 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"로봇청소기 청소 구역 조회 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}
    
    @tool
    def set_robot_cleaner_area(area: Annotated[str, "로봇청소기 청소 구역"]):
        """로봇청소기가 청소할 구역을 설정합니다."""
        logger.info(f"로봇청소기 청소 구역 설정 도구 호출됨: {area}")
        url = f"{MOCK_SERVER_URL}/robot-cleaner/area"
        payload = {"area": area}
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info(f"로봇청소기 청소 구역 설정 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"로봇청소기 청소 구역 설정 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}
    
    @tool
    def get_robot_cleaner_schedule():
        """로봇청소기의 현재 스케줄을 조회합니다."""
        logger.info("로봇청소기 스케줄 조회 도구 호출됨")
        url = f"{MOCK_SERVER_URL}/robot-cleaner/schedule"
        try:
            response = requests.get(url)
            response.raise_for_status()
            result = response.json()
            logger.info(f"로봇청소기 스케줄 조회 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"로봇청소기 스케줄 조회 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}
    
    @tool
    def set_robot_cleaner_schedule(schedule: Annotated[Dict, "로봇청소기 청소 스케줄"]):
        """로봇청소기의 스케줄을 설정합니다."""
        logger.info(f"로봇청소기 청소 스케줄 설정 도구 호출됨: {schedule}")
        url = f"{MOCK_SERVER_URL}/robot-cleaner/schedule"
        payload = {"schedule": schedule}
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            result = response.json()
            logger.info(f"로봇청소기 청소 스케줄 설정 결과: {result}")
            return result
        except requests.exceptions.RequestException as e:
            error_msg = f"로봇청소기 청소 스케줄 설정 실패: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            return {"error": error_msg}

def get_robot_cleaner_tools():
    """로봇청소기 관련 도구들을 반환합니다."""
    logger.info("로봇청소기 도구 모음 로드됨")
    return [
        RobotCleanerTools.get_robot_cleaner_state,
        RobotCleanerTools.set_robot_cleaner_state,
        RobotCleanerTools.get_robot_cleaner_mode,
        RobotCleanerTools.set_robot_cleaner_mode,
        RobotCleanerTools.get_robot_cleaner_mode_list,
        RobotCleanerTools.get_robot_cleaner_battery,
        RobotCleanerTools.get_robot_cleaner_area,
        RobotCleanerTools.set_robot_cleaner_area,
        RobotCleanerTools.get_robot_cleaner_schedule,
        RobotCleanerTools.set_robot_cleaner_schedule
    ] 