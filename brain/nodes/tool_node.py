"""
brain/nodes/tool_node.py — 도구 실행 노드 모듈

LLM이 결정한 도구(tool_call)를 실행하고,
결과를 ToolMessage로 변환하여 그래프 상태에 추가하는 노드입니다.
"""

from langgraph.prebuilt import ToolNode as LangGraphToolNode
from loguru import logger


def create_tool_node(tools: list):
    """도구 실행 노드를 생성합니다.

    LangGraph의 내장 ToolNode를 사용하여 도구 실행 노드를 생성합니다.
    ToolNode는 마지막 AIMessage의 tool_calls를 파싱하여
    해당 도구를 실행하고, 결과를 ToolMessage로 래핑합니다.

    Args:
        tools: 실행 가능한 도구 목록 (BaseTool 리스트)

    Returns:
        LangGraph ToolNode 인스턴스
    """
    logger.info("Tool 노드 생성 — 등록된 도구 수: {}", len(tools))

    # LangGraph 내장 ToolNode 사용
    # - 자동으로 AIMessage.tool_calls 파싱
    # - 도구 실행 후 ToolMessage 생성
    # - 에러 발생 시 에러 메시지를 ToolMessage로 반환
    tool_node = LangGraphToolNode(tools)

    return tool_node
