from typing import Literal, Annotated, TypedDict, List, Dict, Any, Optional, Union, Callable, cast
from typing_extensions import TypedDict

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage, BaseMessage
from langchain_google_vertexai import ChatVertexAI
from langgraph.graph import MessagesState, StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.runnables import RunnableConfig
import json
import os
import datetime
import time
from PIL import Image
from io import BytesIO
import traceback
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.agents import AgentExecutor
from dotenv import load_dotenv
import matplotlib.pyplot as plt
import matplotlib.image as mpimg
import networkx as nx
import glob
import asyncio

# 로깅 설정 가져오기
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from logging_config import setup_logger

# 로거 설정
logger = setup_logger("supervisor")

from agents.agents import create_routine_agent, create_device_agent, create_robot_cleaner_agent

# 멀티에이전트 메시지 상태 정의
class SmartHomeState(TypedDict):
    """스마트홈 멀티에이전트 시스템의 상태"""
    messages: List[BaseMessage]
    next: Optional[str]

# 라우팅 결정 클래스 정의 - Vertex AI 함수 호출 형식에 맞게 수정
class Router(TypedDict):
    """다음에 실행할 에이전트 결정"""
    next: str  # "routine_agent", "device_agent", "robot_cleaner_agent", "FINISH" 중 하나

# 각 에이전트 메모리
AGENT_MEMORY = {}

# 슈퍼바이저 모델 초기화
def get_supervisor_llm():
    """슈퍼바이저용 Vertex AI 모델을 초기화합니다."""
    logger.info("슈퍼바이저 LLM 초기화 시작")
    try:
        # 구조화된 출력을 위한 스키마
        router_schema = {
            "type": "object",
            "properties": {
                "next": {
                    "type": "string",
                    "enum": ["routine_agent", "device_agent", "robot_cleaner_agent", "FINISH"],
                    "description": "다음에 실행할 에이전트 또는 종료 명령"
                }
            },
            "required": ["next"]
        }
        
        logger.info("Vertex AI 모델 로드 시도")
        model_name = os.getenv("MODEL_NAME", "gemini-1.5-pro")
        llm = ChatVertexAI(
            model_name=model_name,
            temperature=0,
            convert_system_message_to_human=True,
        )
        # 구조화된 출력 형식으로 직접 설정
        llm._function_call_schema = router_schema
        
        logger.info("슈퍼바이저 LLM 초기화 성공")
        return llm
    except Exception as e:
        error_msg = f"슈퍼바이저 Vertex AI 모델 초기화 중 오류: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        logger.warning("슈퍼바이저에 로컬 테스트 모드로 전환합니다...")
        from langchain_community.llms import FakeListLLM
        from langchain_core.prompts import ChatPromptTemplate
        
        # 슈퍼바이저 결정을 시뮬레이션하는 장치
        class FakeSupervisorLLM:
            def with_structured_output(self, schema):
                logger.info("FakeSupervisorLLM: 구조화된 출력 요청")
                return self
                
            def invoke(self, messages, config=None):
                # 마지막 메시지 확인
                last_message = None
                agent_name = None
                
                for msg in reversed(messages):
                    if hasattr(msg, 'name') and msg.name in ['routine_agent', 'device_agent', 'robot_cleaner_agent']:
                        last_message = msg.content.lower()
                        agent_name = msg.name
                        break
                
                # 기본값은 새 요청이거나 에이전트가 아직 응답하지 않은 경우
                if not last_message or not agent_name:
                    # 새 사용자 메시지가 루틴 요청인지, 로봇청소기 요청인지 확인
                    user_message = messages[-1].content.lower() if messages else ""
                    if "루틴" in user_message or "routine" in user_message:
                        logger.info("FakeSupervisorLLM: 루틴 에이전트로 라우팅")
                        return {"next": "routine_agent"}
                    elif "로봇" in user_message or "청소기" in user_message or "robot" in user_message or "cleaner" in user_message:
                        logger.info("FakeSupervisorLLM: 로봇청소기 에이전트로 라우팅")
                        return {"next": "robot_cleaner_agent"}
                    else:
                        logger.info("FakeSupervisorLLM: 디바이스 에이전트로 라우팅")
                        return {"next": "device_agent"}
                
                # 에이전트 응답 분석
                if agent_name == "routine_agent":
                    # 루틴 에이전트가 목록을 반환했거나 작업 완료를 표시한 경우
                    if ("등록되었습니다" in last_message or 
                        "삭제되었습니다" in last_message or "제안" in last_message):
                        logger.info("FakeSupervisorLLM: 루틴 작업 완료, FINISH 반환")
                        return {"next": "FINISH"}
                    # '루틴 목록'이 있더라도, 실제 목록 내용이 포함되어 있는지 확인
                    elif "루틴 목록" in last_message and "입니다" in last_message:
                        logger.info("FakeSupervisorLLM: 루틴 목록 조회 완료, FINISH 반환")
                        return {"next": "FINISH"}
                    else:
                        logger.info("FakeSupervisorLLM: 루틴 작업 계속, 루틴 에이전트로 반환")
                        return {"next": "routine_agent"}
                elif agent_name == "device_agent":
                    # 디바이스 에이전트가 상태 변경 또는 조회를 완료한 경우
                    if ("변경되었습니다" in last_message or "설정되었습니다" in last_message or 
                        "현재 상태" in last_message or "온도" in last_message):
                        logger.info("FakeSupervisorLLM: 디바이스 작업 완료, FINISH 반환")
                        return {"next": "FINISH"}
                    else:
                        logger.info("FakeSupervisorLLM: 디바이스 작업 계속, 디바이스 에이전트로 반환")
                        return {"next": "device_agent"}
                elif agent_name == "robot_cleaner_agent":
                    # 로봇청소기 에이전트가 상태 변경 또는 조회를 완료한 경우
                    if ("변경되었습니다" in last_message or "설정되었습니다" in last_message or 
                        "현재 상태" in last_message or "모드" in last_message):
                        logger.info("FakeSupervisorLLM: 로봇청소기 작업 완료, FINISH 반환")
                        return {"next": "FINISH"}
                    else:
                        logger.info("FakeSupervisorLLM: 로봇청소기 작업 계속, 로봇청소기 에이전트로 반환")
                        return {"next": "robot_cleaner_agent"}
                
                # 기본값은 디바이스 에이전트
                logger.info("FakeSupervisorLLM: 기본값, 디바이스 에이전트로 라우팅")
                return {"next": "device_agent"}
        
        return FakeSupervisorLLM()

# 슈퍼바이저 시스템 프롬프트 정의
SUPERVISOR_SYSTEM_PROMPT = """당신은 스마트홈 시스템의 슈퍼바이저 에이전트입니다. 사용자의 요청을 분석하여 적절한 에이전트에 작업을 할당합니다.

당신은 다음 세 가지 에이전트 중 하나를 선택해야 합니다:
1. routine_agent: 스마트홈 루틴 관리를 담당합니다. 루틴 등록, 조회, 삭제, 제안 등의 작업을 수행합니다.
2. device_agent: 가전제품(냉장고, 에어컨) 제어를 담당합니다. 전원 제어, 모드 변경, 상태 확인 등의 작업을 수행합니다.
3. robot_cleaner_agent: 로봇청소기 제어를 담당합니다. 로봇청소기의, 전원 제어, 모드 변경, 방범 구역 설정 등의 작업을 수행합니다.

사용자의 요청을 분석하여 다음 중 하나를 선택하세요:
- "routine_agent": 루틴 관련 요청인 경우 (루틴 등록, 조회, 삭제, 제안)
- "device_agent": 냉장고와 에어컨 제어 관련 요청인 경우 (냉장고, 에어컨의 전원, 모드, 상태 변경 등)
- "robot_cleaner_agent": 로봇청소기 제어 관련 요청인 경우 (로봇청소기의 전원, 모드, 방범 구역 설정 등)
- "FINISH": 모든 작업이 완료되어 더 이상 에이전트 호출이 필요 없는 경우

에이전트 선택 기준:
- 사용자가 루틴에 대해 언급하거나 루틴 관련 작업을 요청하는 경우 -> routine_agent
- 사용자가 로봇청소기에 대해 언급하거나 로봇청소기 관련 작업을 요청하는 경우 -> robot_cleaner_agent
- 사용자가 냉장고나 에어컨 제어를 요청하는 경우 -> device_agent
- 이전 에이전트의 응답만으로 사용자의 요청이 완료된 경우 -> FINISH

항상 정확하고 명확한 결정을 내려주세요.
"""

# 슈퍼바이저 노드 정의
def supervisor_node(state: SmartHomeState, config: RunnableConfig):
    """슈퍼바이저 노드 구현"""
    request_id = f"req-{time.time()}"
    logger.info(f"[{request_id}] 슈퍼바이저 노드 시작")
    
    # 메시지 로깅
    if state["messages"]:
        last_message = state["messages"][-1]
        logger.info(f"[{request_id}] 마지막 메시지: {last_message.content[:100]}..." if len(last_message.content) > 100 else last_message.content)
    
    # 슈퍼바이저 LLM 초기화
    logger.info(f"[{request_id}] 슈퍼바이저 LLM 가져오기")
    llm = get_supervisor_llm()
    
    # 현재 메시지 목록
    messages = [
        SystemMessage(content=SUPERVISOR_SYSTEM_PROMPT),
    ] + state["messages"]
    
    logger.info(f"[{request_id}] 총 {len(messages)} 개의 메시지로 슈퍼바이저에 요청")
    
    try:
        # LLM에게 라우팅 결정 요청
        logger.info(f"[{request_id}] 슈퍼바이저 LLM 호출 시작")
        start_time = time.time()
        response = llm.with_structured_output(Router).invoke(messages, config)
        elapsed_time = time.time() - start_time
        logger.info(f"[{request_id}] 슈퍼바이저 LLM 응답 (소요시간: {elapsed_time:.2f}초): {response}")
        
        # 다음 에이전트 결정
        goto = response["next"]
        logger.info(f"[{request_id}] 슈퍼바이저 결정: {goto}")
        
        if goto == "FINISH":
            # END 노드로 명시적 라우팅
            logger.info(f"[{request_id}] 작업 완료, END 노드로 라우팅")
            return {"next": END}
        
        # 다음 노드 반환
        logger.info(f"[{request_id}] 다음 노드: {goto}")
        return {"next": goto}
    except Exception as e:
        error_msg = f"슈퍼바이저 결정 중 오류 발생: {str(e)}"
        logger.error(f"[{request_id}] {error_msg}")
        logger.error(f"[{request_id}] {traceback.format_exc()}")
        # 오류 발생 시 기본값으로 device_agent 반환
        logger.warning(f"[{request_id}] 오류 발생으로 기본값(device_agent) 반환")
        return {"next": "device_agent"}

# 루틴 에이전트 노드 정의
def routine_agent_node(state: SmartHomeState, config: RunnableConfig):
    """루틴 에이전트 노드 구현"""
    request_id = f"req-{time.time()}"
    logger.info(f"[{request_id}] 루틴 에이전트 노드 시작")
    
    # 루틴 에이전트 초기화
    logger.info(f"[{request_id}] 루틴 에이전트 초기화")
    agent = create_routine_agent()
    
    # 사용자 쿼리 추출
    user_message = state["messages"][-1].content if state["messages"] else ""
    logger.info(f"[{request_id}] 사용자 쿼리: {user_message[:100]}..." if len(user_message) > 100 else user_message)
    
    try:
        # 에이전트 실행 - LangGraph 에이전트 호출 방식으로 변경
        logger.info(f"[{request_id}] 루틴 에이전트 실행 시작")
        start_time = time.time()
        response = agent.invoke(
            # LangGraph 에이전트는 messages 형식의 입력을 받습니다
            {"messages": [HumanMessage(content=user_message)]},
            config
        )
        elapsed_time = time.time() - start_time
        logger.info(f"[{request_id}] 루틴 에이전트 응답 (소요시간: {elapsed_time:.2f}초)")
        
        # 응답에서 마지막 메시지 추출
        last_message = response["messages"][-1] if "messages" in response else None
        response_text = last_message.content if last_message else str(response)
        logger.info(f"[{request_id}] 응답 내용: {response_text[:100]}..." if len(response_text) > 100 else response_text)
        
        # 새로운 메시지 목록 생성 (기존 메시지 + 에이전트 응답)
        new_messages = list(state["messages"])
        new_messages.append(HumanMessage(content=response_text, name="routine_agent"))
        logger.info(f"[{request_id}] 루틴 에이전트 완료, 슈퍼바이저로 반환")
        
        # 상태 업데이트 및 다음 노드 반환
        return {
            "messages": new_messages,
            "next": "supervisor"
        }
    except Exception as e:
        error_msg = f"루틴 에이전트 실행 중 오류 발생: {str(e)}"
        logger.error(f"[{request_id}] {error_msg}")
        logger.error(f"[{request_id}] {traceback.format_exc()}")
        
        # 오류 발생 시 오류 메시지를 응답으로 추가
        error_response = f"루틴 처리 중 오류가 발생했습니다: {str(e)}"
        new_messages = list(state["messages"])
        new_messages.append(HumanMessage(content=error_response, name="routine_agent"))
        
        return {
            "messages": new_messages,
            "next": "supervisor"
        }


# 가전제품 제어 에이전트 노드 정의
def device_agent_node(state: SmartHomeState, config: RunnableConfig):
    """가전제품 제어 에이전트 노드 구현"""
    request_id = f"req-{time.time()}"
    logger.info(f"[{request_id}] 가전제품 제어 에이전트 노드 시작")
    
    # 가전제품 제어 에이전트 초기화
    logger.info(f"[{request_id}] 가전제품 제어 에이전트 초기화")
    agent = create_device_agent()
    
    # 사용자 쿼리 추출
    user_message = state["messages"][-1].content if state["messages"] else ""
    logger.info(f"[{request_id}] 사용자 쿼리: {user_message[:100]}..." if len(user_message) > 100 else user_message)
    
    try:
        # 에이전트 실행 - LangGraph 에이전트 호출 방식으로 변경
        logger.info(f"[{request_id}] 가전제품 제어 에이전트 실행 시작")
        start_time = time.time()
        response = agent.invoke(
            # LangGraph 에이전트는 messages 형식의 입력을 받습니다
            {"messages": [HumanMessage(content=user_message)]},
            config
        )
        elapsed_time = time.time() - start_time
        logger.info(f"[{request_id}] 가전제품 제어 에이전트 응답 (소요시간: {elapsed_time:.2f}초)")
        
        # 응답에서 마지막 메시지 추출
        last_message = response["messages"][-1] if "messages" in response else None
        response_text = last_message.content if last_message else str(response)
        logger.info(f"[{request_id}] 응답 내용: {response_text[:100]}..." if len(response_text) > 100 else response_text)
        
        # 새로운 메시지 목록 생성 (기존 메시지 + 에이전트 응답)
        new_messages = list(state["messages"])
        new_messages.append(HumanMessage(content=response_text, name="device_agent"))
        logger.info(f"[{request_id}] 가전제품 제어 에이전트 완료, 슈퍼바이저로 반환")
        
        # 상태 업데이트 및 다음 노드 반환
        return {
            "messages": new_messages,
            "next": "supervisor"
        }
    except Exception as e:
        error_msg = f"가전제품 제어 에이전트 실행 중 오류 발생: {str(e)}"
        logger.error(f"[{request_id}] {error_msg}")
        logger.error(f"[{request_id}] {traceback.format_exc()}")
        
        # 오류 발생 시 오류 메시지를 응답으로 추가
        error_response = f"가전제품 제어 중 오류가 발생했습니다: {str(e)}"
        new_messages = list(state["messages"])
        new_messages.append(HumanMessage(content=error_response, name="device_agent"))
        
        return {
            "messages": new_messages,
            "next": "supervisor"
        }

# 로봇청소기 제어 에이전트 노드 정의
async def robot_cleaner_agent_node_async(state: SmartHomeState):
    """로봇청소기 에이전트 노드의 비동기 구현: 로봇청소기 제어 처리"""
    logger.info("로봇청소기 에이전트 노드 비동기 실행")
    
    # 로봇청소기 에이전트가 이미 생성되어 있는지 확인
    if "robot_cleaner_agent" not in AGENT_MEMORY:
        logger.info("로봇청소기 에이전트 생성 시작 (비동기)")
        try:
            # 로봇청소기 에이전트 비동기 생성
            AGENT_MEMORY["robot_cleaner_agent"] = await create_robot_cleaner_agent()
            logger.info("로봇청소기 에이전트 생성 완료 (비동기)")
        except Exception as e:
            logger.error(f"로봇청소기 에이전트 생성 실패: {str(e)}")
            logger.error(traceback.format_exc())
            error_message = AIMessage(
                content=f"죄송합니다. 로봇청소기 에이전트를 초기화하는 중에 오류가 발생했습니다: {str(e)}",
                name="robot_cleaner_agent"
            )
            return {"messages": state["messages"] + [error_message], "next": None}
    
    # 로봇청소기 에이전트 실행
    try:
        # create_react_agent로 생성된 에이전트 실행
        result = await AGENT_MEMORY["robot_cleaner_agent"].ainvoke({
            "messages": state["messages"]  # 메시지 이력만 전달
        })
        response_content = result.get("output", "")
        
        logger.info(f"로봇청소기 에이전트 응답: {response_content[:200]}..." if len(response_content) > 200 else response_content)
        
        # 에이전트 응답 메시지 생성
        agent_message = AIMessage(content=response_content, name="robot_cleaner_agent")
        
        # 상태 업데이트
        return {"messages": state["messages"] + [agent_message], "next": None}
    except Exception as e:
        logger.error(f"로봇청소기 에이전트 실행 중 오류 발생: {str(e)}")
        logger.error(traceback.format_exc())
        
        # 오류 응답 메시지 생성
        error_message = AIMessage(
            content=f"죄송합니다. 로봇청소기 에이전트 실행 중에 오류가 발생했습니다: {str(e)}",
            name="robot_cleaner_agent"
        )
        
        # 상태 업데이트
        return {"messages": state["messages"] + [error_message], "next": None}

# 동기식 래퍼 함수
def robot_cleaner_agent_node(state: SmartHomeState, config: RunnableConfig):
    """로봇청소기 에이전트 노드: 로봇청소기 제어 처리 (동기식 래퍼)"""
    logger.info("로봇청소기 에이전트 노드 실행 (동기 래퍼)")
    
    # 이벤트 루프 가져오기
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # 이벤트 루프가 없는 경우 새로 생성
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    # 비동기 함수 실행
    return loop.run_until_complete(robot_cleaner_agent_node_async(state))

# 그래프 이미지 저장 함수
def save_graph_as_image(graph, filename=None):
    """
    컴파일된 그래프를 이미지로 저장합니다.
    
    Args:
        graph: 컴파일된 그래프 객체
        filename: 저장할 파일명 (없으면 현재 시간 기반으로 자동 생성)
    
    Returns:
        저장된 파일 경로 또는 텍스트 형식의 그래프
    """
    logger.info("그래프 이미지 저장 시작")
    # 그래프 이미지 디렉토리 생성
    graph_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "graph_img")
    os.makedirs(graph_dir, exist_ok=True)
    
    # 파일명 생성 (현재 시간 기반)
    if not filename:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"smart_home_graph_{timestamp}.png"
    
    # 파일 경로 설정
    filepath = os.path.join(graph_dir, filename)
    logger.info(f"그래프 이미지 경로: {filepath}")
    
    # 그래프를 이미지로 변환하여 저장
    try:
        # mermaid PNG 생성 시도
        logger.info("mermaid PNG 생성 시도")
        try:
            png_data = graph.get_graph().draw_mermaid_png()
            
            # PNG 데이터를 파일로 저장
            with open(filepath, "wb") as f:
                f.write(png_data)
            
            logger.info(f"그래프 이미지가 저장되었습니다: {filepath}")
            return filepath
        except Exception as e:
            logger.warning(f"PNG 생성 실패, 대체 텍스트 형식으로 시도합니다: {str(e)}")
            
            # 대체: 텍스트 형식 (mermaid)으로 저장
            text_filename = filename.replace(".png", ".mmd")
            text_filepath = os.path.join(graph_dir, text_filename)
            
            # 그래프를 mermaid 텍스트로 저장
            mermaid_text = graph.get_graph().draw_mermaid()
            with open(text_filepath, "w", encoding="utf-8") as f:
                f.write(mermaid_text)
                
            logger.info(f"그래프 텍스트가 저장되었습니다: {text_filepath}")
            return text_filepath
            
    except Exception as e:
        error_msg = f"그래프 저장 중 오류 발생: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        
        # 실패 시 그래프 구조를 텍스트로 반환
        try:
            logger.info("그래프 구조 텍스트 반환 시도")
            return str(graph.get_graph())
        except:
            return f"그래프 변환 실패: {error_msg}"

# 스마트홈 그래프 생성
def create_smart_home_graph():
    """스마트홈 멀티에이전트 시스템의 그래프를 생성합니다."""
    logger.info("스마트홈 그래프 생성 시작")
    
    try:
        # LangGraph 임포트
        from langgraph.graph import StateGraph, END
        
        # 그래프 빌더 생성
        logger.info("StateGraph 객체 생성")
        workflow = StateGraph(SmartHomeState)
        
        # 노드 추가
        logger.info("그래프에 노드 추가: supervisor, routine_agent, device_agent, robot_cleaner_agent")
        workflow.add_node("supervisor", supervisor_node)
        workflow.add_node("routine_agent", routine_agent_node)
        workflow.add_node("device_agent", device_agent_node)
        workflow.add_node("robot_cleaner_agent", robot_cleaner_agent_node)
        
        # 시작 노드 설정
        logger.info("시작 노드 설정: supervisor")
        workflow.set_entry_point("supervisor")
        
        # 에이전트 → 슈퍼바이저 엣지 추가
        logger.info("에이전트 → 슈퍼바이저 엣지 추가")
        workflow.add_edge("routine_agent", "supervisor")
        workflow.add_edge("device_agent", "supervisor")
        workflow.add_edge("robot_cleaner_agent", "supervisor")
        
        # 슈퍼바이저 → 에이전트 또는 종료 조건부 엣지 추가
        logger.info("슈퍼바이저 → 에이전트 또는 종료 조건부 엣지 추가")
        workflow.add_conditional_edges(
            "supervisor",
            lambda state: state["next"],
            {
                "routine_agent": "routine_agent",
                "device_agent": "device_agent",
                "robot_cleaner_agent": "robot_cleaner_agent",
                END: END
            }
        )
        
        # 그래프 컴파일
        logger.info("그래프 컴파일 시작")
        graph = workflow.compile()
        logger.info("그래프 컴파일 완료")
        
        # 그래프 이미지 저장 - 기존 이미지가 없을 때만 저장
        graph_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "graph_img")
        image_files = glob.glob(os.path.join(graph_dir, "*.png"))
        if not image_files:
            logger.info("기존 그래프 이미지가 없습니다. 새 이미지를 생성합니다.")
            save_graph_as_image(graph)
        else:
            logger.info("기존 그래프 이미지가 있습니다. 이미지 생성을 건너뜁니다.")
        
        logger.info("멀티에이전트 그래프 생성 완료")
        return graph
    except Exception as e:
        error_msg = f"멀티에이전트 그래프 생성 중 오류 발생: {str(e)}"
        logger.error(error_msg)
        logger.error(traceback.format_exc())
        raise 