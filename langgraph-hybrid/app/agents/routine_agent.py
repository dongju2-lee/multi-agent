import os
from typing import Literal

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import MessagesState
from langgraph.types import Command
from langchain_google_vertexai import ChatVertexAI
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from logging_config import setup_logger

# 도구 가져오기
from tools.routine_tools import register_routine, list_routines, delete_routine, suggest_routine

# 로거 설정
logger = setup_logger("routine_agent")

# 환경 변수 로드
load_dotenv()

# 싱글톤 인스턴스
_agent_instance = None


def get_routine_agent():
    """루틴 관리 에이전트의 싱글톤 인스턴스를 반환합니다."""
    global _agent_instance
    if _agent_instance is None:
        model_name = os.getenv("MODEL_NAME", "gemini-2.5-pro-exp-03-25")
        logger.info(f"루틴 관리 에이전트 LLM 초기화: {model_name}")
        
        # LLM 초기화
        llm = ChatVertexAI(
            model=model_name,
            temperature=0.1,
            max_output_tokens=2048
        )
        
        # 루틴 관리 도구 준비
        tools = [register_routine, list_routines, delete_routine, suggest_routine]
        
        # 시스템 프롬프트 설정
        system_prompt = (
            "당신은 스마트홈 시스템의 루틴을 관리하는 전문가입니다. "
            "사용자의 일상 활동에 맞는 자동화 루틴을 생성, 관리하고 실행을 도와줍니다. "
            "사용자가 루틴을 요청하면 적절한 루틴을 제안하고 등록할 수 있습니다. "
            "기존 루틴을 수정하거나 삭제하는 도움도 제공할 수 있습니다."
            "\n\n"
            "응답 시 항상 한국어로 답변하세요."
        )
        
        # ReAct 에이전트 생성
        _agent_instance = create_react_agent(
            llm, 
            tools, 
            prompt=system_prompt
        )
        
        logger.info("루틴 관리 에이전트 초기화 완료")
        
    return _agent_instance


def routine_node(state: MessagesState) -> Command[Literal["supervisor"]]:
    """
    루틴 관리 에이전트 노드 함수입니다.
    
    Args:
        state: 현재 메시지와 상태 정보
        
    Returns:
        슈퍼바이저로 돌아가는 명령
    """
    # 에이전트 인스턴스 가져오기
    routine_agent = get_routine_agent()
    
    # 에이전트 호출
    logger.info("루틴 관리 에이전트 호출")
    result = routine_agent.invoke(state)
    
    # 결과 메시지 생성
    last_message = result["messages"][-1]
    routine_message = HumanMessage(content=last_message.content, name="routine_agent")
    
    logger.info(f"루틴 관리 에이전트 작업 완료, 슈퍼바이저로 반환")
    
    # 슈퍼바이저로 돌아가기
    return Command(
        update={"messages": [routine_message]},
        goto="supervisor"
    ) 