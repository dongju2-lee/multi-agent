import os
import asyncio
import json
from typing import Literal, List

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import MessagesState
from langgraph.types import Command
from langchain_google_vertexai import ChatVertexAI
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from logging_config import setup_logger
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# 로거 설정
logger = setup_logger("routine_agent")

# 환경 변수 로드
load_dotenv()

# 싱글톤 인스턴스
_agent_instance = None
_mcp_client = None


async def init_mcp_client():
    """MCP 클라이언트를 초기화합니다."""
    global _mcp_client
    if _mcp_client is None:
        logger.info("MCP 클라이언트 초기화 시작")
        
        # MCP 서버 설정
        mcp_config = {
            "routine": {
                "url": os.environ.get("ROUTINE_MCP_URL", "http://0.0.0.0:8007/sse"),
                "transport": "sse",
            },
        }
        logger.info(f"MCP 서버 설정: {json.dumps(mcp_config, indent=2)}")
        
        try:
            # MCP 클라이언트 생성
            logger.info("MCP 클라이언트 생성 중...")
            client = MultiServerMCPClient(mcp_config)
            logger.info("MCP 클라이언트 인스턴스 생성 완료")
            
            # MCP 클라이언트 연결
            logger.info("MCP 서버에 연결 시도 중...")
            await client.__aenter__()
            logger.info("MCP 서버 연결 성공")
            
            _mcp_client = client
            logger.info("MCP 클라이언트 초기화 완료")
        except Exception as e:
            logger.error(f"MCP 클라이언트 초기화 중 오류 발생: {str(e)}")
            raise
    
    return _mcp_client


async def get_tools_with_details() -> List:
    """MCP 도구를 가져오고 상세 정보를 로깅합니다."""
    client = await init_mcp_client()
    
    logger.info("MCP 도구 가져오는 중...")
    tools = client.get_tools()
    
    # 도구 정보 로깅
    logger.info(f"총 {len(tools)}개의 MCP 도구를 가져왔습니다")
    for i, tool in enumerate(tools, 1):
        try:
            tool_name = getattr(tool, "name", f"Tool-{i}")
            tool_desc = getattr(tool, "description", "설명 없음")
            logger.info(f"  도구 {i}: {tool_name} - {tool_desc}")
        except Exception as e:
            logger.warning(f"  도구 {i}의 정보를 가져오는 중 오류: {str(e)}")
    
    return tools


async def get_routine_agent_async():
    """루틴 관리 에이전트의 싱글톤 인스턴스를 비동기적으로 생성합니다."""
    global _agent_instance
    if _agent_instance is None:
        logger.info("루틴 관리 에이전트 초기화 시작")
        
        # 모델 설정 가져오기
        model_name = os.environ.get("ROUTINE_MODEL", "gemini-2.5-pro-exp-03-25")
        logger.info(f"루틴 관리 에이전트 LLM 모델: {model_name}")
        
        try:
            # LLM 초기화
            logger.info("LLM 초기화 중...")
            llm = ChatVertexAI(
                model=model_name,
                temperature=0.1,
                max_output_tokens=20000
            )
            logger.info("LLM 초기화 완료")
            
            # MCP 클라이언트 및 도구 가져오기
            logger.info("MCP 도구 로딩 중...")
            tools = await get_tools_with_details()
            logger.info("MCP 도구 로딩 완료")
            
            # 시스템 프롬프트 설정
            logger.info("시스템 프롬프트 구성 중...")
            system_prompt = ChatPromptTemplate.from_messages([
        ("system", """스마트홈 루틴 관리 에이전트입니다. 당신은 사용자의 일상생활을 더 편리하게 만드는 스마트홈 루틴을 관리합니다.

당신은 다음과 같은 작업을 수행할 수 있습니다:
1. 새로운 루틴 등록
2. 기존 루틴 목록 조회
3. 루틴 삭제
4. 새로운 루틴 제안

사용자가 요청한 작업을 수행하기 위해 적절한 MCP 도구를 사용하세요. 
사용자가 루틴 생성을 요청하면, 적절한 이름과 단계별 작업 흐름을 포함하여 등록하세요.
루틴의 각 단계는 가전제품의 동작을 명확히 설명해야 합니다.

루틴 목록을 조회했을 때는 반드시 조회한 루틴 목록을 자세히 보여주세요. 단순히 "목록을 확인했습니다"라고 응답하지 말고,
실제 루틴의 이름과 세부 내용을 포함하여 명확하게 보여주세요. 

도구 호출 결과에 루틴 정보가 포함되어 있을 경우, 그 정보를 그대로 사용자에게 전달해야 합니다.
결과가 빈 목록이라면 "현재 등록된 루틴이 없습니다"라고 명확히 알려주세요.

예시 루틴 형식:
- 이름: "아침 루틴"
- 흐름: 
  1. 에어컨을 켠다
  2. 에어컨 온도를 24도로 설정한다
  3. 로봇청소기를 켠다
  4. 냉장고 모드를 일반 모드로 변경한다

사용자가 루틴 제안을 요청하면, 사용자의 설명을 바탕으로 적절한 루틴을 제안하세요.
모든 응답은 명확하고 친절하게 제공하세요.

응답은 항상 한국어로 제공하세요.
"""),
        MessagesPlaceholder(variable_name="messages"),
    ])
            logger.info("시스템 프롬프트 설정 완료")
            
            # ReAct 에이전트 생성
            logger.info("ReAct 에이전트 생성 중...")
            _agent_instance = create_react_agent(
                llm, 
                tools, 
                prompt=system_prompt
            )
            logger.info("ReAct 에이전트 생성 완료")
            
            logger.info("루틴 관리 에이전트 초기화 완료")
        except Exception as e:
            logger.error(f"루틴 관리 에이전트 초기화 중 오류 발생: {str(e)}")
            raise
        
    return _agent_instance


def get_routine_agent():
    """루틴 관리 에이전트의 싱글톤 인스턴스를 반환합니다."""
    global _agent_instance
    if _agent_instance is None:
        try:
            # 비동기 초기화 함수를 동기적으로 실행
            logger.info("루틴 에이전트 비동기 초기화 시작")
            loop = asyncio.get_event_loop()
            _agent_instance = loop.run_until_complete(get_routine_agent_async())
            logger.info("루틴 에이전트 비동기 초기화 완료")
        except Exception as e:
            logger.error(f"루틴 에이전트 초기화 실패: {str(e)}")
            raise
    
    return _agent_instance


def routine_node(state: MessagesState) -> Command[Literal["supervisor"]]:
    """
    루틴 관리 에이전트 노드 함수입니다.
    
    Args:
        state: 현재 메시지와 상태 정보
        
    Returns:
        슈퍼바이저로 돌아가는 명령
    """
    try:
        # 에이전트 인스턴스 가져오기
        logger.info("루틴 관리 에이전트 노드 함수 실행 시작")
        routine_agent = get_routine_agent()
        
        # 입력 메시지 로깅
        if "messages" in state and state["messages"]:
            last_user_msg = state["messages"][-1].content
            logger.info(f"루틴 에이전트에 전달된 메시지: '{last_user_msg[:1000]}...'")
        
        # 에이전트 호출
        logger.info("루틴 관리 에이전트 추론 시작")
        result = routine_agent.invoke(state)
        logger.info("루틴 관리 에이전트 추론 완료")
        
        # 결과 메시지 생성
        if "messages" in result and result["messages"]:
            last_message = result["messages"][-1]
            routine_message = HumanMessage(content=last_message.content, name="routine_agent")
            logger.info(f"루틴 에이전트 응답: '{last_message.content[:1000]}...'")
        else:
            logger.warning("루틴 에이전트가 응답을 생성하지 않음")
            routine_message = HumanMessage(content="응답을 생성할 수 없습니다.", name="routine_agent")
        
        logger.info("루틴 관리 에이전트 작업 완료, 슈퍼바이저로 반환")
        
        # 슈퍼바이저로 돌아가기
        return Command(
            update={"messages": [routine_message]},
            goto="supervisor"
        )
    except Exception as e:
        logger.error(f"루틴 관리 노드 함수 실행 중 오류 발생: {str(e)}")
        error_message = HumanMessage(
            content=f"루틴 관리 에이전트 실행 중 오류가 발생했습니다: {str(e)}",
            name="routine_agent"
        )
        return Command(
            update={"messages": [error_message]},
            goto="supervisor"
        ) 