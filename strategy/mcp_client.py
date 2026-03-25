"""
strategy/mcp_client.py — MCP 클라이언트 모듈

langchain-mcp-adapters를 사용하여 외부 MCP 서버에 연결하고,
MCP 도구를 LangChain BaseTool로 자동 변환합니다.

핵심 구조:
    - MCPClientManager: MCP 서버 연결/세션 관리
    - MultiServerMCPClient를 통한 다중 서버 동시 연결
    - 설정(AppSettings)에서 MCP 서버 목록을 로드하여 적용
"""

from typing import Any, Optional

from loguru import logger

from config.settings import get_settings
from config.types_dto import MCPServerConfig


class MCPClientManager:
    """MCP 서버 연결 및 도구 동기화 관리자

    langchain-mcp-adapters의 MultiServerMCPClient를 활용하여
    설정된 MCP 서버에 연결하고, 도구 목록을 자동으로 LangChain Tool로 변환합니다.

    사용 예:
        manager = MCPClientManager()
        # 비동기 컨텍스트에서 연결 후 도구 목록 가져오기
        async with manager.connect() as tools:
            print(f"사용 가능한 MCP 도구: {len(tools)}개")
    """

    def __init__(self, server_configs: Optional[list[dict]] = None):
        """MCPClientManager를 초기화합니다.

        Args:
            server_configs: MCP 서버 설정 목록. None이면 AppSettings에서 로드.
        """
        settings = get_settings()
        self._server_configs = server_configs or settings.mcp_servers
        self._tools: list = []
        logger.info("MCPClientManager 초기화 — 서버 수: {}", len(self._server_configs))

    def _build_server_params(self) -> dict[str, dict[str, Any]]:
        """설정에서 MultiServerMCPClient 파라미터를 구성합니다.

        Returns:
            서버별 연결 파라미터 딕셔너리
        """
        params = {}
        for config in self._server_configs:
            # MCPServerConfig DTO로 변환 (유효성 검증)
            try:
                server = MCPServerConfig(**config)
                if not server.enabled:
                    logger.info("MCP 서버 '{}' 비활성화됨 — 건너뜀", server.name)
                    continue

                # stdio 전송 방식 파라미터 구성
                params[server.name] = {
                    "command": server.command,
                    "args": server.args,
                    "transport": "stdio",
                }

                # 환경 변수가 있으면 추가
                if server.env:
                    params[server.name]["env"] = server.env

                logger.info("MCP 서버 등록: {} ({})", server.name, server.command)

            except Exception as e:
                logger.warning("MCP 서버 설정 파싱 실패: {} — {}", config, str(e))
                continue

        return params

    async def get_tools(self) -> list:
        """MCP 서버에 연결하여 사용 가능한 도구 목록을 가져옵니다.

        langchain-mcp-adapters의 MultiServerMCPClient를 사용하여
        비동기로 MCP 서버에 연결하고 도구를 LangChain Tool로 변환합니다.

        Returns:
            LangChain BaseTool 리스트
        """
        server_params = self._build_server_params()

        # 설정된 MCP 서버가 없으면 빈 리스트 반환
        if not server_params:
            logger.info("설정된 MCP 서버가 없습니다 — 빈 도구 목록 반환")
            return []

        try:
            # langchain-mcp-adapters 동적 임포트 (서버 설정 있을 때만)
            from langchain_mcp_adapters.client import MultiServerMCPClient

            async with MultiServerMCPClient(server_params) as client:
                self._tools = client.get_tools()
                logger.info("✅ MCP 도구 {}개 로드 완료", len(self._tools))
                return self._tools

        except ImportError:
            logger.error("langchain-mcp-adapters 패키지가 설치되지 않았습니다")
            return []
        except Exception as e:
            logger.error("MCP 서버 연결 실패: {}", str(e))
            return []

    def get_available_tools(self) -> list:
        """마지막으로 로드된 도구 목록을 반환합니다 (캐시된 결과).

        Returns:
            LangChain BaseTool 리스트 (비동기 연결 전이면 빈 리스트)
        """
        return self._tools
