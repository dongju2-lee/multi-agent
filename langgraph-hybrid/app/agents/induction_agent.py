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
logger = setup_logger("induction_agent")

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
            "induction": {
                "url": os.environ.get("INDUCTION_MCP_URL", "http://0.0.0.0:8002/sse"),
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


async def get_induction_agent_async():
    """인덕션 제어 에이전트의 싱글톤 인스턴스를 비동기적으로 생성합니다."""
    global _agent_instance
    if _agent_instance is None:
        logger.info("인덕션 제어 에이전트 초기화 시작")
        
        # 모델 설정 가져오기
        model_name = os.environ.get("MODEL_NAME", "gemini-2.5-pro-exp-03-25")
        logger.info(f"인덕션 제어 에이전트 LLM 모델: {model_name}")
        
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
            ("system", """당신은 인덕션을 제어하는 스마트홈 에이전트입니다. 
인덕션의 전원 제어, 타이머 설정, 조리 시작 등을 수행할 수 있습니다.

응답은 항상 한국어로 제공하세요. 제공된 MCP 도구를 사용하여 인덕션을 제어하세요."""),
            MessagesPlaceholder(variable_name="messages")
        ])
            
            logger.info("시스템 프롬프트 설정 완료")
            
            # ReAct 에이전트 생성
            logger.info("ReAct 에이전트 생성 중...")
            _agent_instance = create_react_agent(
                llm, 
                tools, 
                prompt=system_prompt,
            )
            logger.info("ReAct 에이전트 생성 완료")
            
            logger.info("인덕션 제어 에이전트 초기화 완료")
        except Exception as e:
            logger.error(f"인덕션 제어 에이전트 초기화 중 오류 발생: {str(e)}")
            raise
        
    return _agent_instance


def get_induction_agent():
    """인덕션 제어 에이전트의 싱글톤 인스턴스를 반환합니다."""
    global _agent_instance
    if _agent_instance is None:
        try:
            # 비동기 초기화 함수를 동기적으로 실행
            logger.info("인덕션 에이전트 비동기 초기화 시작")
            loop = asyncio.get_event_loop()
            _agent_instance = loop.run_until_complete(get_induction_agent_async())
            logger.info("인덕션 에이전트 비동기 초기화 완료")
        except Exception as e:
            logger.error(f"인덕션 에이전트 초기화 실패: {str(e)}")
            raise
    
    return _agent_instance


def induction_node(state: MessagesState) -> Command[Literal["supervisor"]]:
    """
    인덕션 제어 에이전트 노드 함수입니다.
    
    Args:
        state: 현재 메시지와 상태 정보
        
    Returns:
        슈퍼바이저로 돌아가는 명령
    """
    try:
        # 에이전트 인스턴스 가져오기
        logger.info("인덕션 제어 에이전트 노드 함수 실행 시작")
        induction_agent = get_induction_agent()
        
        # 입력 메시지 로깅
        if "messages" in state and state["messages"]:
            last_user_msg = state["messages"][-1].content
            logger.info(f"인덕션 에이전트에 전달된 메시지: '{last_user_msg[:1000]}...'")
        
        # 에이전트 호출
        logger.info("인덕션 제어 에이전트 추론 시작")
        result = induction_agent.invoke(state)
        logger.info("인덕션 제어 에이전트 추론 완료")
        
        # 결과 메시지 생성
        if "messages" in result and result["messages"]:
            last_message = result["messages"][-1]
            induction_message = HumanMessage(content=last_message.content, name="induction_agent")
            logger.info(f"인덕션 에이전트 응답: '{last_message.content[:1000]}...'")
        else:
            logger.warning("인덕션 에이전트가 응답을 생성하지 않음")
            induction_message = HumanMessage(content="응답을 생성할 수 없습니다.", name="induction_agent")
        
        logger.info("인덕션 제어 에이전트 작업 완료, 슈퍼바이저로 반환")
        
        # 슈퍼바이저로 돌아가기
        return Command(
            update={"messages": [induction_message]},
            goto="supervisor"
        )
    except Exception as e:
        logger.error(f"인덕션 노드 함수 실행 중 오류 발생: {str(e)}")
        error_message = HumanMessage(
            content=f"인덕션 에이전트 실행 중 오류가 발생했습니다: {str(e)}",
            name="induction_agent"
        )
        return Command(
            update={"messages": [error_message]},
            goto="supervisor"
        ) 