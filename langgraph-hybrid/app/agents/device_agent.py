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
from tools.device_tools import get_refrigerator_tools, get_air_conditioner_tools, get_all_device_tools

# 로거 설정
logger = setup_logger("device_agent")

# 환경 변수 로드
load_dotenv()

# 싱글톤 인스턴스
_agent_instance = None


def get_device_agent():
    """가전제품 제어 에이전트의 싱글톤 인스턴스를 반환합니다."""
    global _agent_instance
    if _agent_instance is None:
        model_name = os.getenv("MODEL_NAME", "gemini-2.5-pro-exp-03-25")
        logger.info(f"가전제품 제어 에이전트 LLM 초기화: {model_name}")
        
        # LLM 초기화
        llm = ChatVertexAI(
            model=model_name,
            temperature=0.1,
            max_output_tokens=2048
        )
        
        # 모든 가전제품 도구 가져오기
        tools = get_all_device_tools()
        
        # 시스템 프롬프트 설정
        system_prompt = (
            "당신은 스마트홈의 가전제품을 제어하는 전문가입니다. "
            "냉장고, 에어컨 등의 가전제품 상태를 확인하고 제어할 수 있습니다. "
            "사용자의 요청에 따라 적절한 도구를 사용하여 가전제품을 관리하세요."
            "\n\n"
            "응답 시 항상 한국어로 답변하세요."
        )
        
        # ReAct 에이전트 생성
        _agent_instance = create_react_agent(
            llm, 
            tools, 
            prompt=system_prompt
        )
        
        logger.info("가전제품 제어 에이전트 초기화 완료")
        
    return _agent_instance


def device_node(state: MessagesState) -> Command[Literal["supervisor"]]:
    """
    가전제품 제어 에이전트 노드 함수입니다.
    
    Args:
        state: 현재 메시지와 상태 정보
        
    Returns:
        슈퍼바이저로 돌아가는 명령
    """
    # 에이전트 인스턴스 가져오기
    device_agent = get_device_agent()
    
    # 에이전트 호출
    logger.info("가전제품 제어 에이전트 호출")
    result = device_agent.invoke(state)
    
    # 결과 메시지 생성
    last_message = result["messages"][-1]
    device_message = HumanMessage(content=last_message.content, name="device_agent")
    
    logger.info(f"가전제품 제어 에이전트 작업 완료, 슈퍼바이저로 반환")
    
    # 슈퍼바이저로 돌아가기
    return Command(
        update={"messages": [device_message]},
        goto="supervisor"
    ) 