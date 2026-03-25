"""
strategy/tool_registry.py — 도구 통합 레지스트리 모듈

로컬 도구와 MCP 외부 도구를 통합 관리하는 중앙 레지스트리입니다.
도구 등록, 검색, 카테고리 필터링, 활성화/비활성화 기능을 제공합니다.
"""

from typing import Optional

from langchain_core.tools import BaseTool
from loguru import logger

from config.constants import ToolCategory, ToolRiskLevel
from config.types_dto import ToolInfo


class ToolRegistry:
    """로컬 도구 + MCP 도구 통합 관리 레지스트리

    에이전트가 사용할 수 있는 모든 도구를 관리하며,
    카테고리, 위험 등급 기반 필터링과 활성화/비활성화를 지원합니다.

    사용 예:
        registry = ToolRegistry()
        registry.register_tool(my_tool, ToolInfo(name="my_tool", ...))
        tools = registry.get_all_tools()
    """

    def __init__(self):
        """ToolRegistry를 초기화합니다."""
        # 도구 저장소: {도구이름: (BaseTool, ToolInfo)}
        self._tools: dict[str, tuple[BaseTool, ToolInfo]] = {}
        logger.info("ToolRegistry 초기화")

    def register_tool(self, tool: BaseTool, info: ToolInfo) -> None:
        """도구를 레지스트리에 등록합니다.

        Args:
            tool: LangChain BaseTool 인스턴스
            info: 도구 메타데이터 (ToolInfo DTO)
        """
        self._tools[info.name] = (tool, info)
        logger.info(
            "도구 등록: {} [{}] — 위험등급: {}, 출처: {}",
            info.name, info.category.value, info.risk_level.value, info.source
        )

    def register_tools(self, tools: list[tuple[BaseTool, ToolInfo]]) -> None:
        """여러 도구를 한 번에 등록합니다.

        Args:
            tools: (BaseTool, ToolInfo) 튜플 리스트
        """
        for tool, info in tools:
            self.register_tool(tool, info)

    def get_tool(self, name: str) -> Optional[BaseTool]:
        """이름으로 도구를 검색합니다.

        Args:
            name: 도구 이름

        Returns:
            BaseTool 인스턴스 또는 None (찾지 못한 경우)
        """
        entry = self._tools.get(name)
        if entry and entry[1].enabled:
            return entry[0]
        return None

    def get_tools(
        self,
        category: Optional[ToolCategory] = None,
        max_risk_level: Optional[ToolRiskLevel] = None,
        source: Optional[str] = None,
    ) -> list[BaseTool]:
        """조건에 맞는 활성화된 도구 목록을 반환합니다.

        Args:
            category: 필터링할 도구 카테고리 (None=전체)
            max_risk_level: 최대 허용 위험 등급 (None=제한 없음)
            source: 도구 출처 필터 ('local', MCP 서버 이름 등)

        Returns:
            조건에 맞는 활성화된 BaseTool 리스트
        """
        # 위험 등급 순서 (필터링에 사용)
        risk_order = {
            ToolRiskLevel.SAFE: 0,
            ToolRiskLevel.LOW: 1,
            ToolRiskLevel.MEDIUM: 2,
            ToolRiskLevel.HIGH: 3,
            ToolRiskLevel.CRITICAL: 4,
        }

        result = []
        for tool, info in self._tools.values():
            # 비활성화된 도구 제외
            if not info.enabled:
                continue

            # 카테고리 필터
            if category and info.category != category:
                continue

            # 위험 등급 필터
            if max_risk_level:
                if risk_order.get(info.risk_level, 0) > risk_order.get(max_risk_level, 4):
                    continue

            # 출처 필터
            if source and info.source != source:
                continue

            result.append(tool)

        return result

    def get_all_tools(self) -> list[BaseTool]:
        """모든 활성화된 도구를 반환합니다.

        Returns:
            활성화된 모든 BaseTool 리스트 (LangGraph 노드에 제공할 목록)
        """
        return [tool for tool, info in self._tools.values() if info.enabled]

    def enable_tool(self, name: str) -> bool:
        """도구를 활성화합니다.

        Args:
            name: 도구 이름

        Returns:
            성공 여부
        """
        if name in self._tools:
            self._tools[name][1].enabled = True
            logger.info("도구 활성화: {}", name)
            return True
        return False

    def disable_tool(self, name: str) -> bool:
        """도구를 비활성화합니다.

        Args:
            name: 도구 이름

        Returns:
            성공 여부
        """
        if name in self._tools:
            self._tools[name][1].enabled = False
            logger.info("도구 비활성화: {}", name)
            return True
        return False

    def get_tool_info(self, name: str) -> Optional[ToolInfo]:
        """도구의 메타데이터를 반환합니다.

        Args:
            name: 도구 이름

        Returns:
            ToolInfo DTO 또는 None
        """
        entry = self._tools.get(name)
        return entry[1] if entry else None

    def list_tools(self) -> list[ToolInfo]:
        """등록된 모든 도구의 메타데이터 목록을 반환합니다.

        Returns:
            ToolInfo DTO 리스트
        """
        return [info for _, info in self._tools.values()]

    @property
    def tool_count(self) -> int:
        """등록된 도구 수를 반환합니다."""
        return len(self._tools)
