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
logger = logging.getLogger("refrigerator_mcp_server")

# FastMCP 인스턴스 생성
mcp = FastMCP(
    "refrigerator",  # MCP 서버 이름
    instructions="냉장고를 제어하는 도구입니다. 냉장고 디스플레이에 요리 상태 조회 및 레시피 정보 표시 기능을 제공합니다.",
    host="0.0.0.0",  # 모든 IP에서 접속 허용
    port=8003,  # 포트 번호
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

# 냉장고 디스플레이 요리 상태 조회 도구
@mcp.tool()
async def get_cooking_state() -> Dict:
    """
    냉장고 디스플레이의 요리 상태를 조회합니다.
    
    Returns:
        Dict: 요리 상태 정보가 포함된 딕셔너리
    """
    logger.info("냉장고 디스플레이 요리 상태 조회 요청 수신")
    # 모의 서버에 API 요청
    result = await mock_api_request("/refrigerator/cooking-state")
    return result

# 냉장고 디스플레이 레시피 스텝 정보 설정 도구
@mcp.tool()
async def set_cooking_state(step_info: str) -> Dict:
    """
    냉장고 디스플레이에 레시피 스텝 정보를 설정합니다.
    
    Args:
        step_info (str): 설정할 레시피 스텝 정보 (JSON 문자열)
        
    Returns:
        Dict: 작업 결과가 포함된 딕셔너리
    """
    logger.info(f"냉장고 디스플레이 레시피 스텝 정보 설정 요청 수신")
    # 모의 서버에 API 요청
    result = await mock_api_request("/refrigerator/cooking-state", "POST", {"step_info": step_info})
    return result

if __name__ == "__main__":
    # 서버 시작 메시지 출력
    print("냉장고 MCP 서버가 실행 중입니다...")
    
    # SSE 트랜스포트를 사용하여 MCP 서버 시작
    mcp.run(transport="sse") 