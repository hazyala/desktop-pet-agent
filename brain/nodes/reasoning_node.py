from langchain_core.messages import SystemMessage
from langchain_ollama import ChatOllama
from loguru import logger

from brain.graph_state import AgentGraphState
from brain.prompts import SYSTEM_PROMPT
from config.settings import get_settings


def create_reasoning_node(tools: list):
    """reasoning 노드 함수를 생성합니다.

    도구가 바인딩된 LLM을 사용하여 사용자 명령에 대해 추론하고,
    도구 호출 또는 최종 응답을 결정합니다.

    Args:
        tools: LLM에 바인딩할 도구 목록 (BaseTool 리스트)

    Returns:
        LangGraph 노드 함수
    """
    # 설정에서 LLM 파라미터 로드
    settings = get_settings()

    # ChatOllama 인스턴스 생성 및 도구 바인딩
    llm = ChatOllama(
        model=settings.vlm_model,
        base_url=settings.vlm_endpoint,
        temperature=settings.llm_temperature,
    )

    # 도구가 있으면 LLM에 바인딩 (tool_call 생성 가능하도록)
    if tools:
        llm_with_tools = llm.bind_tools(tools)
    else:
        llm_with_tools = llm

    def reasoning_node(state: AgentGraphState) -> dict:
        """LLM을 호출하여 다음 행동을 결정하는 노드

        Args:
            state: 현재 그래프 상태 (messages, iteration_count 등)

        Returns:
            업데이트할 상태 딕셔너리 (messages에 AIMessage 추가)
        """
        logger.info(
            "🧠 Reasoning 노드 실행 — 반복 횟수: {}",
            state.get("iteration_count", 0)
        )

        # 메시지 목록 구성 (시스템 프롬프트 + 기존 대화)
        messages = list(state["messages"])

        # 시스템 프롬프트가 없으면 맨 앞에 추가
        if not messages or not isinstance(messages[0], SystemMessage):
            messages.insert(0, SystemMessage(content=SYSTEM_PROMPT))

        # LLM 호출
        try:
            response = llm_with_tools.invoke(messages)
            logger.info("🧠 LLM 응답 수신 — tool_calls: {}",
                       len(response.tool_calls) if hasattr(response, 'tool_calls') and response.tool_calls else 0)
        except Exception as e:
            logger.error("🧠 LLM 호출 실패: {}", str(e))
            from langchain_core.messages import AIMessage
            response = AIMessage(content=f"LLM 호출 중 오류가 발생했습니다: {str(e)}")

        # 상태 업데이트: messages에 응답 추가, iteration_count 증가
        return {
            "messages": [response],
            "iteration_count": state.get("iteration_count", 0) + 1,
        }

    return reasoning_node
