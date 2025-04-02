import json
import os
import asyncio
import logging
from typing import Any, Dict, List, Optional, Union, Callable
import sseclient
import requests
from langchain.tools import BaseTool
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# 환경 변수 로드
load_dotenv()

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("robot_cleaner_mcp_tools")

# 로봇청소기 MCP 도구 URL을 환경 변수나 기본값으로 설정
ROBOT_CLEANER_MCP_URL = os.getenv("ROBOT_CLEANER_MCP_URL", "http://localhost:8001")


# SSE 이벤트 스트림 처리 함수
def process_sse_stream(url: str) -> Dict[str, Any]:
    """SSE 이벤트 스트림을 처리하여 결과를 반환하는 함수"""
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        client = sseclient.SSEClient(response)
        
        # 첫 번째 이벤트만 가져옴
        event = next(client.events())
        client.close()
        
        # 이벤트 데이터를 JSON으로 파싱
        data = json.loads(event.data)
        return data
    except Exception as e:
        logger.error(f"SSE 스트림 처리 오류: {str(e)}")
        return {"error": str(e)}


# POST 요청을 보내고 SSE 응답을 처리하는 함수
def send_post_request_sse(url: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """POST 요청을 보내고 SSE 응답을 처리하는 함수"""
    try:
        # POST 요청 전송
        headers = {"Content-Type": "application/json"}
        response = requests.post(url, json=data, headers=headers, stream=True)
        response.raise_for_status()
        
        # SSE 클라이언트 초기화
        client = sseclient.SSEClient(response)
        
        # 첫 번째 이벤트만 가져옴
        event = next(client.events())
        client.close()
        
        # 이벤트 데이터를 JSON으로 파싱
        result = json.loads(event.data)
        return result
    except Exception as e:
        logger.error(f"POST 요청 및 SSE 응답 처리 오류: {str(e)}")
        return {"error": str(e)}


# ----- 로봇청소기 MCP 도구 클래스 -----

class GetRobotCleanerStateTool(BaseTool):
    name: str = "get_robot_cleaner_state"
    description: str = "로봇청소기의 현재 상태(켜짐/꺼짐)를 조회합니다."
    
    def _run(self, **kwargs: Any) -> Dict[str, Any]:
        """로봇청소기 상태 조회"""
        url = f"{ROBOT_CLEANER_MCP_URL}/robot-cleaner/state"
        return process_sse_stream(url)
    
    async def _arun(self, **kwargs: Any) -> Dict[str, Any]:
        return self._run(**kwargs)


class SetRobotCleanerStateTool(BaseTool):
    name: str = "set_robot_cleaner_state"
    description: str = "로봇청소기의 상태를 설정합니다. 'on' 또는 'off'로 설정할 수 있습니다."
    
    def _run(self, state: str) -> Dict[str, Any]:
        """로봇청소기 상태 설정
        
        Args:
            state: 설정할 상태 ('on' 또는 'off')
        """
        if state not in ["on", "off"]:
            return {"error": "상태는 'on' 또는 'off'로만 설정 가능합니다."}
        
        url = f"{ROBOT_CLEANER_MCP_URL}/robot-cleaner/state"
        data = {"state": state}
        return send_post_request_sse(url, data)
    
    async def _arun(self, state: str) -> Dict[str, Any]:
        return self._run(state=state)


class GetRobotCleanerModeTool(BaseTool):
    name: str = "get_robot_cleaner_mode"
    description: str = "로봇청소기의 현재 작동 모드를 조회합니다."
    
    def _run(self, **kwargs: Any) -> Dict[str, Any]:
        """로봇청소기 모드 조회"""
        url = f"{ROBOT_CLEANER_MCP_URL}/robot-cleaner/mode"
        return process_sse_stream(url)
    
    async def _arun(self, **kwargs: Any) -> Dict[str, Any]:
        return self._run(**kwargs)


class SetRobotCleanerModeTool(BaseTool):
    name: str = "set_robot_cleaner_mode"
    description: str = "로봇청소기의 모드를 설정합니다. 가능한 모드: 'normal', 'turbo', 'silent', 'auto', 'spot', 'patrol'"
    
    def _run(self, mode: str) -> Dict[str, Any]:
        """로봇청소기 모드 설정
        
        Args:
            mode: 설정할 모드
        """
        valid_modes = ["normal", "turbo", "silent", "auto", "spot", "patrol"]
        if mode not in valid_modes:
            return {"error": f"유효하지 않은 모드입니다. 가능한 모드: {', '.join(valid_modes)}"}
        
        url = f"{ROBOT_CLEANER_MCP_URL}/robot-cleaner/mode"
        data = {"mode": mode}
        return send_post_request_sse(url, data)
    
    async def _arun(self, mode: str) -> Dict[str, Any]:
        return self._run(mode=mode)


class GetRobotCleanerModeListTool(BaseTool):
    name: str = "get_robot_cleaner_mode_list"
    description: str = "로봇청소기에서 사용 가능한 모드 목록을 조회합니다."
    
    def _run(self, **kwargs: Any) -> Dict[str, Any]:
        """로봇청소기 모드 목록 조회"""
        url = f"{ROBOT_CLEANER_MCP_URL}/robot-cleaner/mode/list"
        return process_sse_stream(url)
    
    async def _arun(self, **kwargs: Any) -> Dict[str, Any]:
        return self._run(**kwargs)


class GetRobotCleanerFilterUsageTool(BaseTool):
    name: str = "get_robot_cleaner_filter_usage"
    description: str = "로봇청소기 필터의 사용량을 조회합니다. 필터 사용량은 백분율로 표시됩니다."
    
    def _run(self, **kwargs: Any) -> Dict[str, Any]:
        """로봇청소기 필터 사용량 조회"""
        url = f"{ROBOT_CLEANER_MCP_URL}/robot-cleaner/filter"
        return process_sse_stream(url)
    
    async def _arun(self, **kwargs: Any) -> Dict[str, Any]:
        return self._run(**kwargs)


class GetRobotCleanerCountTool(BaseTool):
    name: str = "get_robot_cleaner_count"
    description: str = "로봇청소기의 청소 횟수를 조회합니다."
    
    def _run(self, **kwargs: Any) -> Dict[str, Any]:
        """로봇청소기 청소 횟수 조회"""
        url = f"{ROBOT_CLEANER_MCP_URL}/robot-cleaner/cleaner-count"
        return process_sse_stream(url)
    
    async def _arun(self, **kwargs: Any) -> Dict[str, Any]:
        return self._run(**kwargs)


class GetAvailablePatrolAreasTool(BaseTool):
    name: str = "get_available_patrol_areas"
    description: str = "로봇청소기가 방범 기능을 수행할 수 있는 구역 목록을 조회합니다."
    
    def _run(self, **kwargs: Any) -> Dict[str, Any]:
        """로봇청소기 방범 가능 구역 목록 조회"""
        url = f"{ROBOT_CLEANER_MCP_URL}/robot-cleaner/patrol/list"
        return process_sse_stream(url)
    
    async def _arun(self, **kwargs: Any) -> Dict[str, Any]:
        return self._run(**kwargs)


class GetPatrolSettingsTool(BaseTool):
    name: str = "get_patrol_settings"
    description: str = "로봇청소기의 현재 방범 구역 설정을 조회합니다."
    
    def _run(self, **kwargs: Any) -> Dict[str, Any]:
        """로봇청소기 방범 구역 설정 조회"""
        url = f"{ROBOT_CLEANER_MCP_URL}/robot-cleaner/patrol/setting"
        return process_sse_stream(url)
    
    async def _arun(self, **kwargs: Any) -> Dict[str, Any]:
        return self._run(**kwargs)


class SetPatrolAreasTool(BaseTool):
    name: str = "set_patrol_areas"
    description: str = "로봇청소기의 방범 구역을 설정합니다. 설정할 구역 목록을 쉼표로 구분하여 입력합니다."
    
    def _run(self, areas: str) -> Dict[str, Any]:
        """로봇청소기 방범 구역 설정
        
        Args:
            areas: 설정할 방범 구역 목록 (쉼표로 구분, 예: '거실,안방,주방')
        """
        # 쉼표로 구분된 문자열을 리스트로 변환
        area_list = [area.strip() for area in areas.split(",") if area.strip()]
        
        url = f"{ROBOT_CLEANER_MCP_URL}/robot-cleaner/patrol/start"
        data = {"areas": area_list}
        return send_post_request_sse(url, data)
    
    async def _arun(self, areas: str) -> Dict[str, Any]:
        return self._run(areas=areas)


def get_robot_cleaner_mcp_tools() -> List[BaseTool]:
    """로봇청소기 MCP 도구 목록을 반환하는 함수"""
    return [
        GetRobotCleanerStateTool(),
        SetRobotCleanerStateTool(),
        GetRobotCleanerModeTool(),
        SetRobotCleanerModeTool(),
        GetRobotCleanerModeListTool(),
        GetRobotCleanerFilterUsageTool(),
        GetRobotCleanerCountTool(),
        GetAvailablePatrolAreasTool(),
        GetPatrolSettingsTool(),
        SetPatrolAreasTool(),
    ] 