import os
import logging
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from logging_config import setup_logger

# 로거 설정
logger = setup_logger("mcp_client")

# 환경 변수 로드
load_dotenv()

# MCP 서버 URL 가져오기
mcp_server_url = os.getenv("MCP_SERVER_URL", "http://0.0.0.0:8001")
if mcp_server_url.endswith("/sse"):
    mcp_server_url = mcp_server_url[:-4]  # /sse 부분 제거
logger.info(f"MCP 서버 URL: {mcp_server_url}")

# MCP 클라이언트 설정
# RobotCleaner라는 이름의 MCP 서버와 통신하기 위한 설정
mcp_config = {
    "RobotCleaner": {
        "url": f"{mcp_server_url}/sse",  # SSE 엔드포인트를 사용
        "transport": "sse"           # 서버 전송 이벤트(SSE) 전송 방식 사용
    }
}

logger.info(f"MCP 클라이언트 설정: {mcp_config}")

# MCP 클라이언트 초기화
def init_mcp_client():
    """MultiServerMCPClient 인스턴스를 초기화하고 반환합니다."""
    try:
        logger.info("MCP 클라이언트 초기화 시작")
        client = MultiServerMCPClient(mcp_config)
        logger.info("MCP 클라이언트 초기화 성공")
        return client
    except Exception as e:
        logger.error(f"MCP 클라이언트 초기화 실패: {str(e)}")
        raise

# MCP 도구 가져오기
def get_mcp_tools():
    """MCP 서버에서 제공하는 도구를 가져옵니다."""
    try:
        logger.info("MCP 도구 가져오기 시작")
        client = init_mcp_client()
        # 모든 MCP 도구를 가져옵니다
        tools = client.get_tools()
        logger.info(f"MCP 도구 가져오기 성공: {len(tools)}개 도구 발견")
        return tools
    except Exception as e:
        logger.error(f"MCP 도구 가져오기 실패: {str(e)}")
        raise

# MCP 서버 연결 정보 가져오기
def get_connection_info():
    """MCP 서버 연결 정보를 가져옵니다."""
    return {
        "server_url": mcp_server_url,
        "config": mcp_config
    } 