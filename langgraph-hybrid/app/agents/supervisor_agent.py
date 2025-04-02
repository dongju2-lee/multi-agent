import os
from typing import Literal
from typing_extensions import TypedDict

from langchain_core.messages import SystemMessage
from langgraph.graph import MessagesState, END
from langgraph.types import Command
from langchain_google_vertexai import ChatVertexAI
from dotenv import load_dotenv
from logging_config import setup_logger

# 로거 설정
logger = setup_logger("supervisor_agent")

# 환경 변수 로드
load_dotenv()

# 슈퍼바이저에서 관리할 에이전트 멤버 목록
members = ["device_agent", "routine_agent", "robot_cleaner_agent"]
# 라우팅 옵션 (모든 멤버 + 종료)
options = members + ["FINISH"]

# 슈퍼바이저 시스템 프롬프트
system_prompt = (
    "당신은 스마트홈 시스템을 관리하는 슈퍼바이저입니다. "
    f"다음 작업자들을 관리하고 작업을 조율합니다: {members}. "
    "사용자의 요청에 따라 다음에 어떤 작업자가 필요한지 결정하세요. "
    "각 작업자는 자신의 작업을 수행하고 결과와 상태를 보고합니다. "
    "모든 작업이 완료되면 'FINISH'로 응답하세요."
    "\n\n"
    "각 에이전트의 역할:"
    "\n- device_agent: 에어컨, 냉장고 등의 가전제품을 제어합니다."
    "\n- routine_agent: 스마트홈 루틴을 관리하고 실행합니다."
    "\n- robot_cleaner_agent: 로봇청소기를 제어하고 청소 일정을 관리합니다."
)

# 싱글톤 인스턴스
_llm_instance = None

class Router(TypedDict):
    """다음에 라우팅할 작업자. 필요한 작업자가 없으면 FINISH로 라우팅합니다."""
    next: Literal[*options]


def get_llm():
    """슈퍼바이저 LLM 모델의 싱글톤 인스턴스를 반환합니다."""
    global _llm_instance
    if _llm_instance is None:
        model_name = os.getenv("MODEL_NAME", "gemini-2.5-pro-exp-03-25")
        logger.info(f"슈퍼바이저 에이전트 LLM 초기화: {model_name}")
        _llm_instance = ChatVertexAI(
            model=model_name,
            temperature=0.1,
            max_output_tokens=2048
        )
    return _llm_instance


class State(MessagesState):
    """메시지 상태와 다음 라우팅 정보를 포함하는 상태 클래스"""
    next: str


def supervisor_node(state: State) -> Command[Literal[*members, "__end__"]]:
    """
    슈퍼바이저 노드 함수입니다. 
    현재 상태에 따라 다음에 실행할 에이전트를 결정합니다.
    
    Args:
        state: 현재 메시지와 상태 정보
        
    Returns:
        다음에 실행할 에이전트 명령
    """
    messages = [
        SystemMessage(content=system_prompt),
    ] + state["messages"]
    
    llm = get_llm()
    response = llm.with_structured_output(Router).invoke(messages)
    goto = response["next"]
    
    logger.info(f"슈퍼바이저 라우팅 결정: {goto}")
    
    if goto == "FINISH":
        goto = END
    
    return Command(goto=goto, update={"next": goto}) 