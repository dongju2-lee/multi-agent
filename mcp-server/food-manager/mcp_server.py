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
logger = logging.getLogger("food_manager_mcp_server")

# FastMCP 인스턴스 생성
mcp = FastMCP(
    "food_manager",  # MCP 서버 이름
    instructions="음식 매니저를 제어하는 도구입니다. 냉장고 내 식재료 조회 및 레시피 추천 기능을 제공합니다.",
    host="0.0.0.0",  # 모든 IP에서 접속 허용
    port=8004,  # 포트 번호
)

# 모의 API 요청 함수
async def mock_api_request(path: str, method: str = "GET", data: Optional[Dict] = None) -> Dict:
    """실제 모의 서버에 API 요청을 보내는 함수"""
    url = f"{MOCK_SERVER_URL}{path}"
    logger.info(f"모의 서버 API 요청: {method} {url}")
    
    try:
        if method.upper() == "GET":
            if data is not None:
                from urllib.parse import urlencode
                url = f"{url}?{urlencode(data)}"
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

# 냉장고 내 식재료 목록 조회 도구
@mcp.tool()
async def get_ingredients() -> Dict:
    """
    냉장고 내 식재료 목록을 조회합니다.
    
    Returns:
        Dict: 냉장고 내 식재료 목록이 포함된 딕셔너리
    """
    logger.info("냉장고 내 식재료 목록 조회 요청 수신")
    # 모의 서버에 API 요청
    result = await mock_api_request("/food-manager/ingredients")
    return result

# 식재료 기반 레시피 조회 도구
@mcp.tool()
async def get_recipe(ingredients: List[str]) -> Dict:
    """
    주어진 식재료를 기반으로 레시피를 조회합니다.
    
    Args:
        ingredients (List[str]): 레시피 검색에 사용할 식재료 목록
        
    Returns:
        Dict: 레시피 정보가 포함된 딕셔너리
    """
    logger.info(f"식재료 기반 레시피 조회 요청 수신: {ingredients}")
    # 모의 서버에 API 요청
    result = await mock_api_request("/food-manager/recipe", "GET", {"ingredients": ingredients})
    return result

if __name__ == "__main__":
    # 서버 시작 메시지 출력
    print("음식 매니저 MCP 서버가 실행 중입니다...")
    
    # SSE 트랜스포트를 사용하여 MCP 서버 시작
    mcp.run(transport="sse") 