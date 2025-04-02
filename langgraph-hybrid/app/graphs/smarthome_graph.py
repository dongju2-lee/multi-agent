import os
from langgraph.graph import StateGraph, START, END

from agents.supervisor_agent import supervisor_node, State
from agents.device_agent import device_node
from agents.routine_agent import routine_node
from agents.robot_cleaner_agent import robot_cleaner_node
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
        builder.add_node("device_agent", device_node)
        builder.add_node("routine_agent", routine_node)
        builder.add_node("robot_cleaner_agent", robot_cleaner_node)
        
        # 그래프 컴파일
        _graph_instance = builder.compile()
        
        logger.info("스마트홈 에이전트 그래프 초기화 완료")
        
    return _graph_instance


def get_mermaid_graph():
    """스마트홈 에이전트 그래프의 Mermaid 다이어그램 이미지를 생성합니다."""
    graph = get_smarthome_graph()
    return graph.get_graph().draw_mermaid_png() 