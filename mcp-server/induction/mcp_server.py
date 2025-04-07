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
logger = logging.getLogger("induction_mcp_server")

# FastMCP 인스턴스 생성
mcp = FastMCP(
    "induction",  # MCP 서버 이름
    instructions="인덕션을 제어하는 도구입니다. 전원 상태 확인, 전원 상태 변경, 조리 시작 등의 기능을 제공합니다.",
    host="0.0.0.0",  # 모든 IP에서 접속 허용
    port=8002,  # 포트 번호
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

# 인덕션 전원 상태 조회 도구
@mcp.tool()
async def get_induction_state() -> Dict:
    """
    인덕션의 현재 전원 상태를 조회합니다.
    
    Returns:
        Dict: 인덕션 전원 상태 정보가 포함된 딕셔너리
    """
    logger.info("인덕션 전원 상태 조회 요청 수신")
    # 모의 서버에 API 요청
    result = await mock_api_request("/Induction/power/state")
    return result

# 인덕션 전원 상태 설정 도구
@mcp.tool()
async def set_induction_state(power_state: str) -> Dict:
    """
    인덕션의 전원 상태를 설정합니다.
    
    Args:
        power_state (str): 설정할 전원 상태 ('on' 또는 'off')
        
    Returns:
        Dict: 작업 결과가 포함된 딕셔너리
    """
    logger.info(f"인덕션 전원 상태 설정 요청 수신: {power_state}")
    # 모의 서버에 API 요청
    result = await mock_api_request("/Induction/power/state", "POST", {"power_state": power_state})
    return result

# 인덕션 조리 시작 도구
@mcp.tool()
async def start_cooking(timer: int) -> Dict:
    """
    인덕션 조리를 시작하고 타이머를 설정합니다.
    
    Args:
        timer (int): 설정할 조리 시간 (초 단위)
        
    Returns:
        Dict: 작업 결과가 포함된 딕셔너리
    """
    logger.info(f"인덕션 조리 시작 요청 수신: 타이머 {timer}초")
    # 모의 서버에 API 요청
    result = await mock_api_request("/Induction/start-cooking", "POST", {"timer": timer})
    return result

if __name__ == "__main__":
    # 서버 시작 메시지 출력
    print("인덕션 MCP 서버가 실행 중입니다...")
    
    # SSE 트랜스포트를 사용하여 MCP 서버 시작
    mcp.run(transport="sse") 