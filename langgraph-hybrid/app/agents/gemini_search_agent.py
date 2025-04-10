import os
import asyncio
import json
from typing import Literal, List

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import MessagesState
from langgraph.types import Command
from langchain_google_vertexai import ChatVertexAI
from dotenv import load_dotenv
from logging_config import setup_logger
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# 로거 설정
logger = setup_logger("gemini_search_agent")

# 환경 변수 로드
load_dotenv()

# 싱글톤 인스턴스
_agent_instance = None


async def get_gemini_search_agent_async():
    """Gemini 검색 에이전트의 싱글톤 인스턴스를 비동기적으로 생성합니다."""
    global _agent_instance
    if _agent_instance is None:
        logger.info("Gemini 검색 에이전트 초기화 시작")
        
        # 모델 설정 가져오기
        model_name = os.environ.get("MODEL_NAME", "gemini-2.5-pro-exp-03-25")
        logger.info(f"Gemini 검색 에이전트 LLM 모델: {model_name}")
        
        try:
            # LLM 초기화
            logger.info("LLM 초기화 중...")
            llm = ChatVertexAI(
                model=model_name,
                temperature=0.1,
                max_output_tokens=20000
            )
            logger.info("LLM 초기화 완료")
            
            # 시스템 프롬프트 설정
            logger.info("시스템 프롬프트 구성 중...")
            system_prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 검색 에이전트입니다. 사용자가 제공하는 질문이나 키워드에 대해 정확하고 유용한 정보를 제공해야 합니다.

당신의 역할:
1. 사용자의 질문을 정확히 이해하고 분석합니다.
2. 질문과 관련된 사실적이고 유용한 정보를 제공합니다.
3. 불확실한 사항에 대해서는 정직하게 불확실성을 표현합니다.
4. 복잡한 주제도 이해하기 쉽게 설명합니다.

검색 유형:
- 일반 지식 검색: 역사, 과학, 예술, 스포츠 등 일반적인 지식에 대한 답변
- 최신 정보 검색: 최신 기술 트렌드, 개발 방법론 등에 대한 정보 제공
- 개념 설명: 복잡한 개념이나 용어에 대한 명확한 설명 제공
- 요약 제공: 길거나 복잡한 주제에 대한 간결한 요약 제공

모든 응답은 명확하고 정확하며 유용하게 제공하세요.
불명확한 질문에 대해서는 추가 정보를 요청하여 더 정확한 답변을 제공할 수 있도록 하세요.

응답은 항상 한국어로 제공하세요.
"""),
            MessagesPlaceholder(variable_name="messages")
        ])
            logger.info("시스템 프롬프트 설정 완료")
            
            # 에이전트 생성 (도구 없이 직접 LLM 사용)
            logger.info("Gemini 검색 에이전트 생성 중...")
            _agent_instance = llm
            logger.info("Gemini 검색 에이전트 생성 완료")
            
            logger.info("Gemini 검색 에이전트 초기화 완료")
        except Exception as e:
            logger.error(f"Gemini 검색 에이전트 초기화 중 오류 발생: {str(e)}")
            raise
        
    return _agent_instance


def get_gemini_search_agent():
    """Gemini 검색 에이전트의 싱글톤 인스턴스를 반환합니다."""
    global _agent_instance
    if _agent_instance is None:
        try:
            # 비동기 초기화 함수를 동기적으로 실행
            logger.info("Gemini 검색 에이전트 비동기 초기화 시작")
            loop = asyncio.get_event_loop()
            _agent_instance = loop.run_until_complete(get_gemini_search_agent_async())
            logger.info("Gemini 검색 에이전트 비동기 초기화 완료")
        except Exception as e:
            logger.error(f"Gemini 검색 에이전트 초기화 실패: {str(e)}")
            raise
    
    return _agent_instance


async def gemini_search_node(state: MessagesState) -> Command[Literal["supervisor"]]:
    """
    Gemini 검색 에이전트 노드 함수입니다.
    
    Args:
        state: 현재 메시지와 상태 정보
        
    Returns:
        슈퍼바이저로 돌아가는 명령
    """
    try:
        # 에이전트 인스턴스 가져오기
        logger.info("Gemini 검색 에이전트 노드 함수 실행 시작")
        gemini_search_agent = get_gemini_search_agent()
        
        # 입력 메시지 로깅
        if "messages" in state and state["messages"]:
            last_user_msg = state["messages"][-1].content
            logger.info(f"Gemini 검색 에이전트에 전달된 메시지: '{last_user_msg[:1000]}...'")
        
        # 시스템 프롬프트 구성
        system_prompt = """당신은 검색 에이전트입니다. 사용자가 제공하는 질문이나 키워드에 대해 정확하고 유용한 정보를 제공해야 합니다.

당신의 역할:
1. 사용자의 질문을 정확히 이해하고 분석합니다.
2. 질문과 관련된 사실적이고 유용한 정보를 제공합니다.
3. 불확실한 사항에 대해서는 정직하게 불확실성을 표현합니다.
4. 복잡한 주제도 이해하기 쉽게 설명합니다.

검색 유형:
- 일반 지식 검색: 역사, 과학, 예술, 스포츠 등 일반적인 지식에 대한 답변
- 최신 정보 검색: 최신 기술 트렌드, 개발 방법론 등에 대한 정보 제공
- 개념 설명: 복잡한 개념이나 용어에 대한 명확한 설명 제공
- 요약 제공: 길거나 복잡한 주제에 대한 간결한 요약 제공

모든 응답은 명확하고 정확하며 유용하게 제공하세요.
불명확한 질문에 대해서는 추가 정보를 요청하여 더 정확한 답변을 제공할 수 있도록 하세요.

응답은 항상 한국어로 제공하세요."""
        
        # 메시지 구성
        messages = [
            SystemMessage(content=system_prompt)
        ] + state["messages"]
        
        # 에이전트 호출 (직접 LLM 호출)
        logger.info("Gemini 검색 에이전트 추론 시작")
        response = await gemini_search_agent.ainvoke(messages)
        logger.info("Gemini 검색 에이전트 추론 완료")
        
        # 결과 메시지 생성
        search_message = HumanMessage(content=response.content, name="gemini_search_agent")
        logger.info(f"Gemini 검색 에이전트 응답: '{response.content[:300]}...'")
        
        logger.info("Gemini 검색 에이전트 작업 완료, 슈퍼바이저로 반환")
        
        # 슈퍼바이저로 돌아가기
        return Command(
            update={"messages": [search_message]},
            goto="supervisor"
        )
    except Exception as e:
        logger.error(f"Gemini 검색 노드 함수 실행 중 오류 발생: {str(e)}")
        error_message = HumanMessage(
            content=f"Gemini 검색 에이전트 실행 중 오류가 발생했습니다: {str(e)}",
            name="gemini_search_agent"
        )
        return Command(
            update={"messages": [error_message]},
            goto="supervisor"
        ) 