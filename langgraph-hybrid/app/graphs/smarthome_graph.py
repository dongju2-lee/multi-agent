import os
import io
import requests
from PIL import Image
import base64
from langgraph.graph import StateGraph, START, END

from agents.supervisor_agent import supervisor_node, State
from agents.routine_agent import routine_node
from agents.induction_agent import induction_node
from agents.refrigerator_agent import refrigerator_node
from agents.food_manager_agent import food_manager_node
from agents.microwave_agent import microwave_node
from agents.gemini_search_agent import gemini_search_node
from logging_config import setup_logger

# 로거 설정
logger = setup_logger("smarthome_graph")

# 싱글톤 인스턴스
_graph_instance = None


def get_smarthome_graph():
    """스마트홈 에이전트 그래프의 싱글톤 인스턴스를 반환합니다."""
    global _graph_instance
    if _graph_instance is None:
        logger.info("스마트홈 에이전트 그래프 초기화 시작")
        
        # 그래프 빌더 생성
        builder = StateGraph(State)
        
        # 시작점에서 슈퍼바이저로 연결
        builder.add_edge(START, "supervisor")
        
        # 노드 추가
        builder.add_node("supervisor", supervisor_node)
        builder.add_node("routine_agent", routine_node)
        # 로봇 클리너 노드는 더 이상 사용하지 않음
        builder.add_node("induction_agent", induction_node)
        builder.add_node("refrigerator_agent", refrigerator_node)
        builder.add_node("food_manager_agent", food_manager_node)
        builder.add_node("microwave_agent", microwave_node)
        builder.add_node("gemini_search_agent", gemini_search_node)
        
        # 그래프 컴파일
        _graph_instance = builder.compile()
        
        logger.info("스마트홈 에이전트 그래프 초기화 완료")
        
    return _graph_instance


def get_mermaid_graph():
    """스마트홈 에이전트 그래프의 Mermaid 다이어그램 이미지를 생성합니다."""
    try:
        logger.info("Mermaid 다이어그램 이미지 생성 시작")
        graph = get_smarthome_graph()
        # 타임아웃 없이 기본 호출
        return graph.get_graph().draw_mermaid_png()
    except Exception as e:
        # 오류 발생 시 로그만 남기고 예외 다시 발생시킴
        logger.error(f"Mermaid 다이어그램 생성 실패: {str(e)}")
        raise 