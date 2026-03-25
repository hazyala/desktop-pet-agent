"""
brain/graph_state.py — LangGraph 그래프 상태 정의 모듈

LangGraph의 모든 노드에서 공유하는 상태 객체(TypedDict)를 정의합니다.
messages, screen_state, iteration_count 등을 포함합니다.
"""

from typing import Annotated, Optional, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from config.constants import AgentStatus
from config.types_dto import ActionResult, ScreenState, TaskRequest


class AgentGraphState(TypedDict):
    """LangGraph 그래프 전체에서 공유되는 상태 객체

    모든 노드(reasoning_node, tool_node)가 이 상태를 읽고 쓰며,
    에이전트의 인지-추론-행동 순환 루프를 구동합니다.

    Attributes:
        messages: LLM과의 대화 기록 (HumanMessage, AIMessage, ToolMessage)
                  add_messages 리듀서를 사용하여 메시지를 누적합니다.
        screen_state: 최신 화면 스냅샷 (Blackboard에서 주입)
        iteration_count: 현재 루프 반복 횟수 (무한루프 방지)
        agent_status: 현재 에이전트 실행 상태
        task_request: 원본 사용자 요청 정보
        action_history: 실행된 도구 결과 이력 목록
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    screen_state: Optional[ScreenState]
    iteration_count: int
    agent_status: str  # AgentStatus 값 (str로 직렬화)
    task_request: Optional[dict]  # TaskRequest를 dict로 직렬화
    action_history: list[dict]  # ActionResult를 dict로 직렬화
