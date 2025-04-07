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
logger = logging.getLogger("microwave_mcp_server")

# FastMCP 인스턴스 생성
mcp = FastMCP(
    "microwave",  # MCP 서버 이름
    instructions="전자레인지를 제어하는 도구입니다. 전원 상태 확인/변경, 모드 확인/변경, 레시피 스텝 설정, 조리 시작 등의 기능을 제공합니다.",
    host="0.0.0.0",  # 모든 IP에서 접속 허용
    port=8005,  # 포트 번호
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

# 전자레인지 전원 상태 조회 도구
@mcp.tool()
async def get_microwave_state() -> Dict:
    """
    전자레인지의 현재 전원 상태를 조회합니다.
    
    Returns:
        Dict: 전자레인지 전원 상태 정보가 포함된 딕셔너리
    """
    logger.info("전자레인지 전원 상태 조회 요청 수신")
    # 모의 서버에 API 요청
    result = await mock_api_request("/microwave/power/state")
    return result

# 전자레인지 전원 상태 설정 도구
@mcp.tool()
async def set_microwave_state(power_state: str) -> Dict:
    """
    전자레인지의 전원 상태를 설정합니다.
    
    Args:
        power_state (str): 설정할 전원 상태 ('on' 또는 'off')
        
    Returns:
        Dict: 작업 결과가 포함된 딕셔너리
    """
    logger.info(f"전자레인지 전원 상태 설정 요청 수신: {power_state}")
    # 모의 서버에 API 요청
    result = await mock_api_request("/microwave/power/state", "POST", {"power_state": power_state})
    return result

# 전자레인지 모드 조회 도구
@mcp.tool()
async def get_microwave_mode() -> Dict:
    """
    전자레인지의 현재 모드를 조회합니다.
    
    Returns:
        Dict: 전자레인지 모드 정보가 포함된 딕셔너리
    """
    logger.info("전자레인지 모드 조회 요청 수신")
    # 모의 서버에 API 요청
    result = await mock_api_request("/microwave/mode")
    return result

# 전자레인지 모드 목록 조회 도구
@mcp.tool()
async def get_microwave_mode_list() -> Dict:
    """
    전자레인지에서 사용 가능한 모드 목록을 조회합니다.
    
    Returns:
        Dict: 사용 가능한 모드 목록이 포함된 딕셔너리
    """
    logger.info("전자레인지 모드 목록 조회 요청 수신")
    # 모의 서버에 API 요청
    result = await mock_api_request("/microwave/mode/list")
    return result

# 전자레인지 모드 설정 도구
@mcp.tool()
async def set_microwave_mode(mode: str) -> Dict:
    """
    전자레인지의 모드를 설정합니다.
    
    Args:
        mode (str): 설정할 모드
        
    Returns:
        Dict: 작업 결과가 포함된 딕셔너리
    """
    logger.info(f"전자레인지 모드 설정 요청 수신: {mode}")
    # 모의 서버에 API 요청
    result = await mock_api_request("/microwave/mode", "POST", {"mode": mode})
    return result

# 전자레인지 레시피 스텝 설정 도구
@mcp.tool()
async def set_recipe_step(step_info: str) -> Dict:
    """
    전자레인지에 레시피 스텝 정보를 설정합니다.
    
    Args:
        step_info (str): 설정할 레시피 스텝 정보 (JSON 문자열)
        
    Returns:
        Dict: 작업 결과가 포함된 딕셔너리
    """
    logger.info(f"전자레인지 레시피 스텝 정보 설정 요청 수신")
    # 모의 서버에 API 요청
    result = await mock_api_request("/microwave/step-info", "POST", {"step_info": step_info})
    return result

# 전자레인지 조리 시작 도구
@mcp.tool()
async def start_cooking(timer: int) -> Dict:
    """
    전자레인지 조리를 시작하고 타이머를 설정합니다.
    
    Args:
        timer (int): 설정할 조리 시간 (초 단위)
        
    Returns:
        Dict: 작업 결과가 포함된 딕셔너리
    """
    logger.info(f"전자레인지 조리 시작 요청 수신: 타이머 {timer}초")
    # 모의 서버에 API 요청
    result = await mock_api_request("/microwave/start-cooking", "POST", {"timer": timer})
    return result

if __name__ == "__main__":
    # 서버 시작 메시지 출력
    print("전자레인지 MCP 서버가 실행 중입니다...")
    
    # SSE 트랜스포트를 사용하여 MCP 서버 시작
    mcp.run(transport="sse") 