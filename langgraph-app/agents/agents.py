from langchain_google_vertexai import ChatVertexAI
from langchain.agents import create_openai_functions_agent
from langchain.agents.format_scratchpad import format_to_openai_functions
from langchain.agents.output_parsers import OpenAIFunctionsAgentOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables import Runnable, RunnablePassthrough
import os
from dotenv import load_dotenv
import time
import traceback
from enum import Enum
from typing import Dict, List, Any, Optional, Tuple, Type
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain_google_vertexai import VertexAI
from langgraph.prebuilt import create_react_agent
from langchain_core.language_models import LLM
from langchain_core.callbacks import BaseCallbackHandler
from logging_config import setup_logger

# 로거 설정
logger = setup_logger("agents")

# Vertex AI 초기화
try:
    import vertexai
    from google.cloud import aiplatform
    
    # 환경 변수 로드
    load_dotenv()
    
    # Vertex AI 설정 가져오기
    PROJECT_ID = os.getenv("VERTEX_PROJECT_ID")
    REGION = os.getenv("VERTEX_REGION", "us-central1")
    
    if PROJECT_ID and REGION:
        logger.info(f"Vertex AI 초기화 시도 (프로젝트: {PROJECT_ID}, 리전: {REGION})")
        try:
            vertexai.init(project=PROJECT_ID, location=REGION)
            logger.info("Vertex AI 초기화 성공")
        except Exception as e:
            logger.error(f"Vertex AI 초기화 실패: {str(e)}")
            logger.error(traceback.format_exc())
    else:
        logger.warning("Vertex AI 초기화에 필요한 환경 변수가 없습니다. (VERTEX_PROJECT_ID, VERTEX_REGION)")
except ImportError:
    logger.warning("vertexai 또는 google.cloud.aiplatform 모듈을 찾을 수 없습니다. Vertex AI를 사용할 수 없습니다.")
except Exception as e:
    logger.error(f"Vertex AI 초기화 중 오류 발생: {str(e)}")

from tools.routine_tools import register_routine, list_routines, delete_routine, suggest_routine
from tools.device_tools import (
    get_refrigerator_tools, 
    get_air_conditioner_tools, 
    get_robot_cleaner_tools
)

# 로깅 콜백 핸들러 정의
class LoggingCallbackHandler(BaseCallbackHandler):
    """에이전트 실행을 로깅하는 콜백 핸들러"""
    
    def __init__(self, agent_name: str):
        self.agent_name = agent_name
        self.logger = logger
    
    def on_chain_start(self, serialized: Dict[str, Any], inputs: Dict[str, Any], **kwargs) -> None:
        self.logger.info(f"{self.agent_name} 체인 시작: {inputs.get('input', '')[:100]}...")
    
    def on_chain_end(self, outputs: Dict[str, Any], **kwargs) -> None:
        output = outputs.get("output", "")
        self.logger.info(f"{self.agent_name} 체인 종료: {output[:100]}...")
    
    def on_chain_error(self, error: Exception, **kwargs) -> None:
        self.logger.error(f"{self.agent_name} 체인 오류: {str(error)}")
        self.logger.error(traceback.format_exc())
    
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        self.logger.info(f"{self.agent_name} LLM 호출 시작")
    
    def on_llm_end(self, response, **kwargs) -> None:
        self.logger.info(f"{self.agent_name} LLM 호출 완료")
    
    def on_llm_error(self, error: Exception, **kwargs) -> None:
        self.logger.error(f"{self.agent_name} LLM 호출 오류: {str(error)}")
        self.logger.error(traceback.format_exc())

# FakeRoutineAgentLLM 클래스
class FakeRoutineAgentLLM(LLM):
    """테스트용 루틴 에이전트 LLM"""
    
    def _call(self, prompt: str, stop=None, **kwargs) -> str:
        logger.info("테스트용 루틴 에이전트 LLM 사용")
        return """
스마트홈 루틴 에이전트입니다. 루틴 관리를 도와드리겠습니다.

현재 등록된 루틴은 다음과 같습니다:
1. 아침 루틴: 오전 7시에 커튼 열기, 조명 켜기, 뉴스 재생
2. 퇴근 루틴: 오후 6시에 에어컨 켜기, 조명 켜기, 음악 재생

무엇을 도와드릴까요?
        """
    
    @property
    def _llm_type(self) -> str:
        return "fake-routine-agent-llm"

# FakeDeviceAgentLLM 클래스
class FakeDeviceAgentLLM(LLM):
    """테스트용 기기 에이전트 LLM"""
    
    def _call(self, prompt: str, stop=None, **kwargs) -> str:
        logger.info("테스트용 기기 에이전트 LLM 사용")
        return """
스마트홈 기기 에이전트입니다. 다음 기기들을 제어할 수 있습니다:
- 에어컨 (거실, 침실)
- 조명 (거실, 침실, 주방)
- TV (거실)
- 로봇청소기
- 냉장고

무엇을 도와드릴까요?
        """
    
    @property
    def _llm_type(self) -> str:
        return "fake-device-agent-llm"

# 루틴 에이전트 생성 함수
def create_routine_agent():
    """루틴 관리 에이전트를 생성합니다."""
    logger.info("루틴 에이전트 생성 시작")
    
    # 루틴 에이전트용 프롬프트 템플릿
    routine_agent_prompt = ChatPromptTemplate.from_messages([
        ("system", """스마트홈 루틴 관리 에이전트입니다. 당신은 사용자의 일상생활을 더 편리하게 만드는 스마트홈 루틴을 관리합니다.

당신은 다음과 같은 작업을 수행할 수 있습니다:
1. 새로운 루틴 등록
2. 기존 루틴 목록 조회
3. 루틴 삭제
4. 새로운 루틴 제안

사용자가 요청한 작업을 수행하기 위해 적절한 도구를 사용하세요. 
사용자가 루틴 생성을 요청하면, 적절한 이름과 단계별 작업 흐름을 포함하여 등록하세요.
루틴의 각 단계는 가전제품의 동작을 명확히 설명해야 합니다.

예시 루틴 형식:
- 이름: "아침 루틴"
- 흐름: 
  1. 에어컨을 켠다
  2. 에어컨 온도를 24도로 설정한다
  3. 로봇청소기를 켠다
  4. 냉장고 모드를 일반 모드로 변경한다

사용자가 루틴 제안을 요청하면, 사용자의 설명을 바탕으로 적절한 루틴을 제안하세요.
모든 응답은 명확하고 친절하게 제공하세요.
"""),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    # 루틴 관리용 도구 목록
    routine_tools = [register_routine, list_routines, delete_routine, suggest_routine]
    
    # Vertex AI 모델 초기화
    try:
        logger.info("루틴 에이전트 LLM 초기화 시도 (Vertex AI)")
        start_time = time.time()
        
        llm = ChatVertexAI(model="gemini-2.0-flash")
        
        end_time = time.time()
        logger.info(f"루틴 에이전트 LLM 초기화 성공 (소요 시간: {end_time - start_time:.2f}초)")
    except Exception as e:
        logger.error(f"루틴 에이전트 LLM 초기화 실패, 테스트 모드로 전환: {str(e)}")
        logger.error(traceback.format_exc())
        
        # 실패 시 테스트용 LLM 사용
        from langchain_community.llms import FakeListLLM
        llm = FakeListLLM(responses=["루틴 관리 요청이 처리되었습니다."])
    
    # 에이전트 생성 - LangGraph의 create_react_agent 사용
    langgraph_agent = create_react_agent(
        model=llm,
        tools=routine_tools,
        prompt=routine_agent_prompt
    )
    
    logger.info("루틴 에이전트 생성 완료")
    return langgraph_agent.with_config({"run_name": "RoutineAgent"})

# 가전제품 제어 에이전트 생성 함수
def create_device_agent():
    """가전제품 제어 에이전트를 생성합니다."""
    logger.info("기기 에이전트 생성 시작")
    
    # 가전제품 제어 에이전트용 프롬프트 템플릿
    device_agent_prompt = ChatPromptTemplate.from_messages([
        ("system", """스마트홈 가전제품 제어 에이전트입니다. 당신은 다양한 스마트홈 가전제품(냉장고, 에어컨, 로봇청소기)을 제어합니다.

당신은 다음과 같은 가전제품을 제어할 수 있습니다:
1. 냉장고: 전원 제어, 모드 변경, 식품 목록 확인 등
2. 에어컨: 전원 제어, 모드 변경, 온도 조절, 필터 사용량 확인 등
3. 로봇청소기: 전원 제어, 모드 변경, 방범 구역 설정, 필터 사용량 확인, 청소 횟수 확인 등

사용자의 요청에 따라 적절한 가전제품과 기능을 선택하여 제어하세요.
항상 현재 상태를 확인한 후 변경하는 것이 좋습니다.
작업 완료 후에는 수행한 작업의 결과를 사용자에게 명확히 알려주세요.

모든 응답은 명확하고 친절하게 제공하세요.
"""),
        MessagesPlaceholder(variable_name="messages"),
    ])
    
    # 각 가전제품 제어용 도구 목록
    refrigerator_tools = get_refrigerator_tools()
    air_conditioner_tools = get_air_conditioner_tools()
    robot_cleaner_tools = get_robot_cleaner_tools()
    
    # 모든 가전제품 도구를 하나로 합침
    device_tools = refrigerator_tools + air_conditioner_tools + robot_cleaner_tools
    
    # Vertex AI 모델 초기화
    try:
        logger.info("기기 에이전트 LLM 초기화 시도 (Vertex AI)")
        start_time = time.time()
        
        llm = ChatVertexAI(model="gemini-2.0-flash")
        
        end_time = time.time()
        logger.info(f"기기 에이전트 LLM 초기화 성공 (소요 시간: {end_time - start_time:.2f}초)")
    except Exception as e:
        logger.error(f"기기 에이전트 LLM 초기화 실패, 테스트 모드로 전환: {str(e)}")
        logger.error(traceback.format_exc())
        
        # 실패 시 테스트용 LLM 사용
        from langchain_community.llms import FakeListLLM
        llm = FakeListLLM(responses=["가전제품 제어 요청이 처리되었습니다."])
    
    # 에이전트 생성 - LangGraph의 create_react_agent 사용
    langgraph_agent = create_react_agent(
        model=llm,
        tools=device_tools,
        prompt=device_agent_prompt
    )
    
    logger.info("기기 에이전트 생성 완료")
    return langgraph_agent.with_config({"run_name": "DeviceAgent"}) 