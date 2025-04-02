from mcp.server.fastmcp import FastMCP
import os
import requests
import json
import logging
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()
MOCK_SERVER_URL = os.getenv("MOCK_SERVER_URL", "http://localhost:8000")

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("robot_cleaner_mcp_server")

# FastMCP 인스턴스 생성
mcp = FastMCP(
    "robot_cleaner",  # MCP 서버 이름
    instructions="로봇청소기를 제어하는 도구입니다. 상태 확인, 모드 변경, 방범 구역 설정 등의 기능을 제공합니다.",
    host="0.0.0.0",  # 모든 IP에서 접속 허용
    port=8001,  # 포트 번호
)

# 모의 API 요청 함수
async def mock_api_request(path: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
    """실제 모의 서버에 API 요청을 보내는 함수"""
    url = f"{MOCK_SERVER_URL}{path}"
    logger.info(f"모의 서버 API 요청: {method} {url}")
    
    try:
        if method.upper() == "GET":
            response = requests.get(url)
        elif method.upper() == "POST":
            response = requests.post(url, json=data)
        else:
            return {"error": f"지원하지 않는 HTTP 메서드: {method}"}
        
        response.raise_for_status()
        result = response.json()
        logger.info(f"모의 서버 응답: {json.dumps(result, ensure_ascii=False)}")
        return result
    except Exception as e:
        logger.error(f"모의 서버 요청 실패: {str(e)}")
        return {"error": f"모의 서버 요청 실패: {str(e)}"}

# 로봇청소기 상태 조회 도구
@mcp.tool()
async def get_robot_cleaner_state() -> Dict:
    """
    로봇청소기의 현재 상태(켜짐/꺼짐)를 조회합니다.
    
    Returns:
        Dict: 로봇청소기 상태 정보가 포함된 딕셔너리
    """
    logger.info("로봇청소기 상태 조회 요청 수신")
    # 모의 서버에 API 요청
    result = await mock_api_request("/robot-cleaner/state")
    return result

# 로봇청소기 상태 설정 도구
@mcp.tool()
async def set_robot_cleaner_state(state: str) -> Dict:
    """
    로봇청소기의 상태를 설정합니다.
    
    Args:
        state (str): 설정할 상태 ('on' 또는 'off')
        
    Returns:
        Dict: 작업 결과가 포함된 딕셔너리
    """
    logger.info(f"로봇청소기 상태 설정 요청 수신: {state}")
    # 모의 서버에 API 요청
    result = await mock_api_request("/robot-cleaner/state", "POST", {"state": state})
    return result

# 로봇청소기 모드 조회 도구
@mcp.tool()
async def get_robot_cleaner_mode() -> Dict:
    """
    로봇청소기의 현재 작동 모드를 조회합니다.
    
    Returns:
        Dict: 로봇청소기 모드 정보가 포함된 딕셔너리
    """
    logger.info("로봇청소기 모드 조회 요청 수신")
    # 모의 서버에 API 요청
    result = await mock_api_request("/robot-cleaner/mode")
    return result

# 로봇청소기 모드 설정 도구
@mcp.tool()
async def set_robot_cleaner_mode(mode: str) -> Dict:
    """
    로봇청소기의 모드를 설정합니다.
    
    Args:
        mode (str): 설정할 모드 (normal, pet, power, auto, patrol 중 하나)
        
    Returns:
        Dict: 작업 결과가 포함된 딕셔너리
    """
    logger.info(f"로봇청소기 모드 설정 요청 수신: {mode}")
    # 모의 서버에 API 요청
    result = await mock_api_request("/robot-cleaner/mode", "POST", {"mode": mode})
    return result

# 로봇청소기 모드 목록 조회 도구
@mcp.tool()
async def get_robot_cleaner_mode_list() -> Dict:
    """
    로봇청소기에서 사용 가능한 모드 목록을 조회합니다.
    
    Returns:
        Dict: 사용 가능한 모드 목록이 포함된 딕셔너리
    """
    logger.info("로봇청소기 모드 목록 조회 요청 수신")
    # 모의 서버에 API 요청
    result = await mock_api_request("/robot-cleaner/mode/list")
    return result

# 로봇청소기 필터 사용량 조회 도구
@mcp.tool()
async def get_robot_cleaner_filter_usage() -> Dict:
    """
    로봇청소기 필터의 사용량을 조회합니다.
    
    Returns:
        Dict: 필터 사용량 정보가 포함된 딕셔너리
    """
    logger.info("로봇청소기 필터 사용량 조회 요청 수신")
    # 모의 서버에 API 요청
    result = await mock_api_request("/robot-cleaner/filter")
    return result

# 로봇청소기 청소 횟수 조회 도구
@mcp.tool()
async def get_robot_cleaner_count() -> Dict:
    """
    로봇청소기의 청소 횟수를 조회합니다.
    
    Returns:
        Dict: 청소 횟수 정보가 포함된 딕셔너리
    """
    logger.info("로봇청소기 청소 횟수 조회 요청 수신")
    # 모의 서버에 API 요청
    result = await mock_api_request("/robot-cleaner/cleaner-count")
    return result

# 로봇청소기 방범 가능 구역 목록 조회 도구
@mcp.tool()
async def get_available_patrol_areas() -> Dict:
    """
    로봇청소기가 방범 기능을 수행할 수 있는 구역 목록을 조회합니다.
    
    Returns:
        Dict: 방범 가능 구역 목록이 포함된 딕셔너리
    """
    logger.info("로봇청소기 방범 가능 구역 목록 조회 요청 수신")
    # 모의 서버에 API 요청
    result = await mock_api_request("/robot-cleaner/patrol/list")
    return result

# 로봇청소기 방범 구역 설정 조회 도구
@mcp.tool()
async def get_patrol_settings() -> Dict:
    """
    로봇청소기의 현재 방범 구역 설정을 조회합니다.
    
    Returns:
        Dict: 현재 방범 구역 설정이 포함된 딕셔너리
    """
    logger.info("로봇청소기 방범 구역 설정 조회 요청 수신")
    # 모의 서버에 API 요청
    result = await mock_api_request("/robot-cleaner/patrol/setting")
    return result

# 로봇청소기 방범 구역 설정 도구
@mcp.tool()
async def set_patrol_areas(areas: List[str]) -> Dict:
    """
    로봇청소기의 방범 구역을 설정합니다.
    
    Args:
        areas (List[str]): 설정할 방범 구역 목록
        
    Returns:
        Dict: 작업 결과가 포함된 딕셔너리
    """
    logger.info(f"로봇청소기 방범 구역 설정 요청 수신: {areas}")
    # 모의 서버에 API 요청
    result = await mock_api_request("/robot-cleaner/patrol/start", "POST", {"areas": areas})
    return result

if __name__ == "__main__":
    # 서버 시작 메시지 출력
    print("로봇청소기 MCP 서버가 실행 중입니다...")
    
    # SSE 트랜스포트를 사용하여 MCP 서버 시작
    mcp.run(transport="sse") 