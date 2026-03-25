"""
config/types_dto.py — 데이터 전송 객체 (DTO) 정의 모듈

시스템 전체에서 사용되는 모든 Pydantic V2 데이터 모델을 정의합니다.
모듈 간 데이터 교환 시 타입 안전성과 직렬화/역직렬화를 보장합니다.
"""

from datetime import datetime
from typing import Any, Optional, Sequence
from uuid import uuid4

from pydantic import BaseModel, Field

from config.constants import AgentStatus, ToolCategory, ToolRiskLevel


# ═══════════════════════════════════════════════════════════════
# 3-1. Sensor 계층 DTO
# ═══════════════════════════════════════════════════════════════

class BoundingBox(BaseModel):
    """OCR이 인식한 텍스트의 화면 위치 정보 (바운딩 박스)"""
    x: int = Field(..., description="좌측 상단 X 좌표 (px)")
    y: int = Field(..., description="좌측 상단 Y 좌표 (px)")
    width: int = Field(..., description="너비 (px)")
    height: int = Field(..., description="높이 (px)")

    @property
    def center(self) -> tuple[int, int]:
        """바운딩 박스의 중심 좌표를 반환합니다."""
        return (self.x + self.width // 2, self.y + self.height // 2)


class OCRTextBlock(BaseModel):
    """OCR로 인식된 개별 텍스트 블록"""
    text: str = Field(..., description="인식된 텍스트 내용")
    bbox: BoundingBox = Field(..., description="텍스트의 화면 위치")
    confidence: float = Field(..., ge=0.0, le=1.0, description="인식 신뢰도 (0~1)")


class OCRResult(BaseModel):
    """OCR 엔진의 전체 인식 결과"""
    text_blocks: list[OCRTextBlock] = Field(
        default_factory=list, description="인식된 텍스트 블록 목록"
    )
    full_text: str = Field(default="", description="모든 블록의 텍스트를 합친 전문")
    captured_at: datetime = Field(
        default_factory=datetime.now, description="캡처 시각"
    )
    resolution: tuple[int, int] = Field(
        default=(0, 0), description="캡처 해상도 (width, height)"
    )

    @property
    def block_count(self) -> int:
        """인식된 텍스트 블록 수를 반환합니다."""
        return len(self.text_blocks)


class ActiveWindowInfo(BaseModel):
    """현재 활성 창(포그라운드 윈도우) 정보"""
    title: str = Field(default="", description="창 제목")
    process_name: str = Field(default="", description="프로세스 이름")
    hwnd: int = Field(default=0, description="윈도우 핸들 (HWND)")
    rect: tuple[int, int, int, int] = Field(
        default=(0, 0, 0, 0),
        description="창 위치 (left, top, right, bottom)"
    )
    is_foreground: bool = Field(default=False, description="포그라운드 여부")


class MouseState(BaseModel):
    """마우스의 현재 위치 상태"""
    x: int = Field(default=0, description="X 좌표")
    y: int = Field(default=0, description="Y 좌표")
    screen_index: int = Field(default=0, description="모니터 인덱스 (멀티모니터)")


class ScreenState(BaseModel):
    """화면 및 시스템 상태의 통합 스냅샷 — Blackboard의 핵심 단위

    센서에서 수집된 모든 정보를 하나의 객체로 통합하여
    Brain(LangGraph)에 전달합니다.
    """
    ocr_result: Optional[OCRResult] = None
    active_window: Optional[ActiveWindowInfo] = None
    mouse_state: Optional[MouseState] = None
    screenshot_path: Optional[str] = Field(None, description="저장된 스크린샷 경로")
    timestamp: datetime = Field(default_factory=datetime.now)


# ═══════════════════════════════════════════════════════════════
# 3-2. Brain / Agent 계층 DTO
# ═══════════════════════════════════════════════════════════════

class TaskRequest(BaseModel):
    """사용자의 자연어 명령 요청"""
    command: str = Field(..., description="사용자의 자연어 명령")
    context: Optional[str] = Field(None, description="추가 컨텍스트 정보")
    max_steps: int = Field(
        default=15, ge=1, le=50, description="최대 실행 스텝 수"
    )
    timeout_seconds: int = Field(
        default=300, ge=10, description="전체 타임아웃 (초)"
    )


class ActionResult(BaseModel):
    """도구 실행 결과"""
    tool_name: str = Field(..., description="실행된 도구 이름")
    success: bool = Field(..., description="성공 여부")
    output: Any = Field(None, description="도구 출력값")
    error_message: Optional[str] = Field(None, description="오류 메시지")
    execution_time_ms: float = Field(
        default=0.0, description="실행 시간 (밀리초)"
    )
    timestamp: datetime = Field(default_factory=datetime.now)


class TaskSummary(BaseModel):
    """태스크 실행 완료 후의 결과 요약"""
    task_id: str = Field(
        default_factory=lambda: str(uuid4()), description="태스크 고유 ID (UUID)"
    )
    command: str = Field(..., description="원본 사용자 명령")
    status: AgentStatus = Field(..., description="최종 실행 상태")
    steps_executed: int = Field(default=0, description="실행된 스텝 수")
    actions: list[ActionResult] = Field(
        default_factory=list, description="실행된 액션 결과 목록"
    )
    final_response: str = Field(
        default="", description="사용자에게 전달할 최종 응답 메시지"
    )
    started_at: datetime = Field(default_factory=datetime.now)
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
# 3-4. MCP / Strategy 계층 DTO
# ═══════════════════════════════════════════════════════════════

class ToolInfo(BaseModel):
    """도구 레지스트리에 등록되는 도구 메타데이터"""
    name: str = Field(..., description="도구 이름")
    description: str = Field(..., description="도구 설명 (LLM에게 제공)")
    category: ToolCategory = Field(..., description="도구 카테고리")
    risk_level: ToolRiskLevel = Field(
        default=ToolRiskLevel.SAFE, description="도구 위험 등급"
    )
    enabled: bool = Field(default=True, description="활성화 여부")
    source: str = Field(
        default="local", description="도구 출처 ('local' 또는 MCP 서버 이름)"
    )


class MCPServerConfig(BaseModel):
    """MCP 서버 연결 설정"""
    name: str = Field(..., description="서버 식별 이름")
    command: str = Field(..., description="서버 실행 명령어")
    args: list[str] = Field(
        default_factory=list, description="실행 인자 목록"
    )
    env: dict[str, str] = Field(
        default_factory=dict, description="환경 변수"
    )
    enabled: bool = Field(default=True, description="활성화 여부")


# ═══════════════════════════════════════════════════════════════
# 3-5. State / Memory 계층 DTO
# ═══════════════════════════════════════════════════════════════

class TaskLogEntry(BaseModel):
    """장기 기억 DB에 저장되는 태스크 실행 로그 항목"""
    id: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    command: str = Field(..., description="사용자 원문 명령")
    target_app: Optional[str] = Field(None, description="대상 애플리케이션")
    status: AgentStatus = Field(..., description="최종 상태")
    error_message: Optional[str] = None
    steps_count: int = Field(default=0, description="수행된 tool call 수")
    execution_time_seconds: float = Field(
        default=0.0, description="총 실행 시간 (초)"
    )
    llm_model: str = Field(default="", description="사용된 LLM 모델명")


# ═══════════════════════════════════════════════════════════════
# 3-6. Kill Switch DTO
# ═══════════════════════════════════════════════════════════════

class KillSwitchEvent(BaseModel):
    """Kill Switch 발동 이벤트 데이터"""
    trigger_type: str = Field(
        ..., description="발동 유형: 'hard_kill' | 'soft_pause' | 'resume'"
    )
    trigger_source: str = Field(
        ..., description="발동 소스: 'mouse_clicks' | 'keyboard_shortcut' | 'ui_button'"
    )
    timestamp: datetime = Field(default_factory=datetime.now)
    agent_status_before: AgentStatus = Field(
        ..., description="이벤트 발생 전 에이전트 상태"
    )
