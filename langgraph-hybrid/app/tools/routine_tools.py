import os
import json
import requests
import traceback
from typing import List, Dict, Annotated
from dotenv import load_dotenv
from langchain_core.tools import tool
from logging_config import setup_logger

# 로거 설정
logger = setup_logger("routine_tools")

# 환경 변수 로드
load_dotenv()
MOCK_SERVER_URL = os.getenv("MOCK_SERVER_URL")

@tool
def register_routine(
    routine_name: Annotated[str, "루틴의 이름"],
    routine_flow: Annotated[List[str], "루틴의 실행 흐름 (단계별 작업 목록)"]
):
    """
    새로운 루틴을 등록합니다.
    
    Args:
        routine_name: 등록할 루틴의 이름
        routine_flow: 루틴의 실행 흐름 (단계별 작업 목록)
    
    Returns:
        등록 결과 메시지
    """
    logger.info(f"새 루틴 등록 도구 호출됨: '{routine_name}' ({len(routine_flow)}개 단계)")
    url = f"{MOCK_SERVER_URL}/routine/register"
    payload = {
        "routine_name": routine_name,
        "routine_flow": routine_flow
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        logger.info(f"루틴 등록 결과: {result}")
        return result
    except requests.exceptions.RequestException as e:
        error_msg = f"루틴 등록 실패: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return {"error": error_msg}

@tool
def list_routines():
    """
    등록된 모든 루틴 목록을 조회합니다.
    
    Returns:
        등록된 루틴 목록
    """
    logger.info("루틴 목록 조회 도구 호출됨")
    url = f"{MOCK_SERVER_URL}/routine/list"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        result = response.json()
        routine_count = len(result.get("routines", {}))
        logger.info(f"루틴 목록 조회 결과: {routine_count}개 루틴 확인됨")
        return result
    except requests.exceptions.RequestException as e:
        error_msg = f"루틴 목록 조회 실패: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return {"error": error_msg}

@tool
def delete_routine(routine_name: Annotated[str, "삭제할 루틴의 이름"]):
    """
    지정된 이름의 루틴을 삭제합니다.
    
    Args:
        routine_name: 삭제할 루틴의 이름
    
    Returns:
        삭제 결과 메시지
    """
    logger.info(f"루틴 삭제 도구 호출됨: '{routine_name}'")
    url = f"{MOCK_SERVER_URL}/routine/delete"
    payload = {
        "routine_name": routine_name
    }
    
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()
        logger.info(f"루틴 삭제 결과: {result}")
        return result
    except requests.exceptions.RequestException as e:
        error_msg = f"루틴 삭제 실패: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        return {"error": error_msg}

@tool
def suggest_routine(
    routine_name: Annotated[str, "제안할 루틴의 이름"],
    routine_description: Annotated[str, "루틴의 목적과 상황 설명"]
):
    """
    사용자의 설명을 기반으로 새로운 루틴을 제안합니다.
    이 도구는 실제로 루틴을 등록하지 않고, 루틴의 단계를 생성하여 제안만 합니다.
    
    Args:
        routine_name: 제안할 루틴의 이름
        routine_description: 루틴의 목적과 상황 설명
    
    Returns:
        제안된 루틴 단계 목록
    """
    logger.info(f"루틴 제안 도구 호출됨: '{routine_name}' - 설명: {routine_description[:50]}..." if len(routine_description) > 50 else routine_description)
    
    # 여기서는 실제 API 호출이 아닌 표준화된 제안 형식을 반환합니다.
    # 실제 제안은 LLM이 수행합니다.
    result = {
        "routine_name": routine_name,
        "suggested_flow": [
            "다음은 제안된 루틴 흐름입니다:",
            "1. 첫번째 단계",
            "2. 두번째 단계",
            "..."
        ],
        "note": "위 흐름은 에이전트가 생성한 제안이며, 실제로 등록하려면 register_routine 도구를 사용하세요."
    }
    
    logger.info(f"루틴 제안 생성 완료: '{routine_name}'")
    return result 