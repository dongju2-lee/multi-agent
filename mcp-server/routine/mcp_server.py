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
logger = logging.getLogger("routine_mcp_server")

# FastMCP 인스턴스 생성
mcp = FastMCP(
    "routine",  # MCP 서버 이름
    instructions="루틴 관리 도구입니다. 루틴 등록, 목록 조회, 삭제 기능을 제공합니다.",
    host="0.0.0.0",  # 모든 IP에서 접속 허용
    port=8007,  # 포트 번호
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

# 루틴 목록 조회 도구
@mcp.tool()
async def get_routines() -> Dict:
    """
    모든 루틴 목록을 조회합니다.
    
    Returns:
        Dict: 루틴 목록이 포함된 딕셔너리
    """
    logger.info("루틴 목록 조회 요청 수신")
    # 모의 서버에 API 요청
    result = await mock_api_request("/routine/list")
    return result

# 루틴 등록 도구
@mcp.tool()
async def register_routine(routine_name: str, routine_flow: List[str]) -> Dict:
    """
    새로운 루틴을 등록합니다.
    
    Args:
        routine_name (str): 등록할 루틴 이름
        routine_flow (List[str]): 루틴 실행 흐름
        
    Returns:
        Dict: 작업 결과가 포함된 딕셔너리
    """
    logger.info(f"루틴 등록 요청 수신: {routine_name}")
    # 모의 서버에 API 요청
    result = await mock_api_request("/routine/register", "POST", {
        "routine_name": routine_name,
        "routine_flow": routine_flow
    })
    return result

# 루틴 삭제 도구
@mcp.tool()
async def delete_routine(routine_name: str) -> Dict:
    """
    지정된 루틴을 삭제합니다.
    
    Args:
        routine_name (str): 삭제할 루틴 이름
        
    Returns:
        Dict: 작업 결과가 포함된 딕셔너리
    """
    logger.info(f"루틴 삭제 요청 수신: {routine_name}")
    # 모의 서버에 API 요청
    result = await mock_api_request("/routine/delete", "POST", {"routine_name": routine_name})
    return result

if __name__ == "__main__":
    # 서버 시작 메시지 출력
    print("루틴 MCP 서버가 실행 중입니다...")
    
    # SSE 트랜스포트를 사용하여 MCP 서버 시작
    mcp.run(transport="sse") 