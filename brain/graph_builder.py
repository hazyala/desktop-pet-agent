"""
brain/graph_builder.py — LangGraph 그래프 빌더 모듈

StateGraph를 구성하여 reasoning → tools → reasoning 순환 루프를 만들고,
조건부 엣지로 도구 호출 여부를 판단합니다.
"""

from langchain_core.messages import AIMessage
from langgraph.graph import END, StateGraph
from loguru import logger

from brain.graph_state import AgentGraphState
from brain.nodes.reasoning_node import create_reasoning_node
from brain.nodes.tool_node import create_tool_node
from config.settings import get_settings
from strategy.local_tools import register_local_tools
from strategy.tool_registry import ToolRegistry


def should_continue(state: AgentGraphState) -> str:
    """조건부 엣지: reasoning 노드 후 다음 행동을 결정합니다.

    1. 마지막 메시지에 tool_calls가 있으면 → "tools" (도구 실행)
    2. max_steps 초과 시 → END (종료)
    3. 그 외 (최종 응답) → END (종료)

    Args:
        state: 현재 그래프 상태

    Returns:
        다음 노드 이름 ("tools" 또는 END)
    """
    messages = state.get("messages", [])
    iteration_count = state.get("iteration_count", 0)
    settings = get_settings()

    # 최대 반복 횟수 초과 시 종료
    if iteration_count >= settings.max_agent_steps:
        logger.warning(
            "⚠️ 최대 반복 횟수({}) 도달 — 에이전트 종료",
            settings.max_agent_steps
        )
        return END

    # 마지막 메시지 확인
    if messages:
        last_message = messages[-1]
        # AIMessage이고 tool_calls가 있으면 도구 실행
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            logger.info(
                "→ tools 노드로 이동 (tool_calls: {}개)",
                len(last_message.tool_calls)
            )
            return "tools"

    # 최종 응답 또는 tool_call 없음 → 종료
    logger.info("→ END — 최종 응답 또는 추가 도구 호출 없음")
    return END


def build_graph(tools: list = None) -> object:
    """LangGraph 에이전트 그래프를 빌드하고 컴파일합니다.

    Args:
        tools: 사용할 도구 목록. None이면 기본 로컬 도구를 등록합니다.

    Returns:
        컴파일된 LangGraph CompiledGraph
    """
    logger.info("LangGraph 에이전트 그래프 빌드 시작")

    # ── 도구 준비 ──
    if tools is None:
        # 기본 로컬 도구 등록
        registry = ToolRegistry()
        register_local_tools(registry)
        tools = registry.get_all_tools()

    logger.info("등록된 도구 수: {}", len(tools))

    # ── 노드 생성 ──
    reasoning = create_reasoning_node(tools)
    tool_executor = create_tool_node(tools)

    # ── StateGraph 구성 ──
    graph = StateGraph(AgentGraphState)

    # 노드 등록
    graph.add_node("reasoning", reasoning)    # LLM 추론 노드
    graph.add_node("tools", tool_executor)    # 도구 실행 노드

    # ── 엣지 정의 ──
    # 시작점 → reasoning
    graph.set_entry_point("reasoning")

    # reasoning → (조건부) tools 또는 END
    graph.add_conditional_edges(
        "reasoning",
        should_continue,
        {
            "tools": "tools",  # tool_call 있으면 → tools
            END: END,          # 최종 응답이면 → 종료
        },
    )

    # tools → reasoning (도구 실행 후 다시 추론)
    graph.add_edge("tools", "reasoning")

    # ── 컴파일 ──
    compiled = graph.compile()
    logger.info("✅ LangGraph 에이전트 그래프 빌드 완료")

    return compiled
