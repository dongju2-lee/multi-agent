import os
import json
from typing import Literal, List

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import MessagesState
from langgraph.types import Command
from langchain_google_vertexai import ChatVertexAI
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from logging_config import setup_logger
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder


# 도구 가져오기
from tools.device_tools import get_refrigerator_tools, get_air_conditioner_tools, get_all_device_tools

# 로거 설정
logger = setup_logger("device_agent")

# 환경 변수 로드
load_dotenv()

# 싱글톤 인스턴스
_agent_instance = None


def get_device_tools_with_details() -> List:
    """가전제품 도구를 가져오고 상세 정보를 로깅합니다."""
    logger.info("가전제품 도구 로딩 시작")
    
    try:
        tools = get_all_device_tools()
        
        # 도구 정보 로깅
        logger.info(f"총 {len(tools)}개의 가전제품 도구를 가져왔습니다")
        for i, tool in enumerate(tools, 1):
            try:
                tool_name = getattr(tool, "name", f"Tool-{i}")
                tool_desc = getattr(tool, "description", "설명 없음")
                logger.info(f"  도구 {i}: {tool_name} - {tool_desc}")
            except Exception as e:
                logger.warning(f"  도구 {i}의 정보를 가져오는 중 오류: {str(e)}")
        
        logger.info("가전제품 도구 로딩 완료")
        return tools
    except Exception as e:
        logger.error(f"가전제품 도구 로딩 중 오류 발생: {str(e)}")
        raise


def get_device_agent():
    """가전제품 제어 에이전트의 싱글톤 인스턴스를 반환합니다."""
    global _agent_instance
    if _agent_instance is None:
        try:
            logger.info("가전제품 제어 에이전트 초기화 시작")
            
            # 모델 설정 가져오기
            model_name = os.getenv("MODEL_NAME", "gemini-2.5-pro-exp-03-25")
            logger.info(f"가전제품 제어 에이전트 LLM 모델: {model_name}")
            
            # LLM 초기화
            logger.info("LLM 초기화 중...")
            llm = ChatVertexAI(
                model=model_name,
                temperature=0.1,
                max_output_tokens=2048
            )
            logger.info("LLM 초기화 완료")
            
            # 모든 가전제품 도구 가져오기
            tools = get_device_tools_with_details()
            
            # 시스템 프롬프트 설정
            logger.info("시스템 프롬프트 구성 중...")
            system_prompt = ChatPromptTemplate.from_messages([
        ("system", """스마트홈 가전제품 제어 에이전트입니다. 당신은 다양한 스마트홈 가전제품(냉장고, 에어컨)을 제어합니다.

당신은 다음과 같은 가전제품을 제어할 수 있습니다:
1. 냉장고: 전원 제어, 모드 변경, 식품 목록 확인 등
2. 에어컨: 전원 제어, 모드 변경, 온도 조절, 필터 사용량 확인 등

사용자의 요청에 따라 적절한 가전제품과 기능을 선택하여 제어하세요.
항상 현재 상태를 확인한 후 변경하는 것이 좋습니다.
작업 완료 후에는 수행한 작업의 결과를 사용자에게 명확히 알려주세요.

참고: 로봇청소기는 별도의 에이전트가 담당하므로 당신은 제어할 수 없습니다.

모든 응답은 명확하고 친절하게 제공하세요.
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
            
            logger.info("가전제품 제어 에이전트 초기화 완료")
        except Exception as e:
            logger.error(f"가전제품 제어 에이전트 초기화 중 오류 발생: {str(e)}")
            raise
        
    return _agent_instance


def device_node(state: MessagesState) -> Command[Literal["supervisor"]]:
    """
    가전제품 제어 에이전트 노드 함수입니다.
    
    Args:
        state: 현재 메시지와 상태 정보
        
    Returns:
        슈퍼바이저로 돌아가는 명령
    """
    try:
        # 에이전트 인스턴스 가져오기
        logger.info("가전제품 제어 에이전트 노드 함수 실행 시작")
        device_agent = get_device_agent()
        
        # 입력 메시지 로깅
        if "messages" in state and state["messages"]:
            last_user_msg = state["messages"][-1].content
            logger.info(f"가전제품 에이전트에 전달된 메시지: '{last_user_msg[:100]}...'")
        
        # 에이전트 호출
        logger.info("가전제품 제어 에이전트 추론 시작")
        result = device_agent.invoke(state)
        logger.info("가전제품 제어 에이전트 추론 완료")
        
        # 결과 메시지 생성
        if "messages" in result and result["messages"]:
            last_message = result["messages"][-1]
            device_message = HumanMessage(content=last_message.content, name="device_agent")
            logger.info(f"가전제품 에이전트 응답: '{last_message.content[:100]}...'")
        else:
            logger.warning("가전제품 에이전트가 응답을 생성하지 않음")
            device_message = HumanMessage(content="응답을 생성할 수 없습니다.", name="device_agent")
        
        logger.info("가전제품 제어 에이전트 작업 완료, 슈퍼바이저로 반환")
        
        # 슈퍼바이저로 돌아가기
        return Command(
            update={"messages": [device_message]},
            goto="supervisor"
        )
    except Exception as e:
        logger.error(f"가전제품 노드 함수 실행 중 오류 발생: {str(e)}")
        error_message = HumanMessage(
            content=f"가전제품 에이전트 실행 중 오류가 발생했습니다: {str(e)}",
            name="device_agent"
        )
        return Command(
            update={"messages": [error_message]},
            goto="supervisor"
        ) 