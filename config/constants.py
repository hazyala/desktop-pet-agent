"""
config/constants.py — 열거형 상수 정의 모듈

에이전트 상태, 도구 카테고리, 위험 등급, 에러 코드 등
시스템 전역에서 사용되는 열거형 상수를 정의합니다.
"""

from enum import Enum


# ═══════════════════════════════════════════════════════════════
# 에이전트 실행 상태 열거형
# ═══════════════════════════════════════════════════════════════
class AgentStatus(str, Enum):
    """에이전트의 현재 실행 상태를 나타내는 열거형"""
    IDLE = "idle"                   # 대기 중
    EXECUTING = "executing"         # 명령 실행 중
    PAUSED = "paused"              # 일시 정지 (Soft Pause)
    DONE = "done"                  # 정상 완료
    FAILED = "failed"              # 실패
    KILLED = "killed"              # 비상 정지됨 (Kill Switch 발동)


# ═══════════════════════════════════════════════════════════════
# 도구 카테고리 열거형
# ═══════════════════════════════════════════════════════════════
class ToolCategory(str, Enum):
    """도구의 기능별 분류 카테고리"""
    HID = "hid"                    # 마우스/키보드 물리 제어
    SENSOR = "sensor"              # 화면 캡처, OCR
    OS = "os"                      # 운영체제 제어
    FILE = "file"                  # 파일 조작
    OFFICE = "office"              # Word/Excel 자동화
    MCP = "mcp"                    # 외부 MCP 서버 도구
    UTIL = "util"                  # 유틸리티 (대기 등)


# ═══════════════════════════════════════════════════════════════
# 도구 위험 등급 열거형
# ═══════════════════════════════════════════════════════════════
class ToolRiskLevel(str, Enum):
    """도구의 부작용 위험도 등급"""
    SAFE = "safe"                  # 읽기 전용, 부작용 없음
    LOW = "low"                    # 경미한 부작용 (클릭, 타이핑)
    MEDIUM = "medium"              # 파일 생성/수정, 문서 편집
    HIGH = "high"                  # 파일 삭제/이동, 시스템 설정 변경
    CRITICAL = "critical"          # 시스템 종료, 대량 파일 조작


# ═══════════════════════════════════════════════════════════════
# 에러 코드 열거형
# ═══════════════════════════════════════════════════════════════
class ErrorCode(str, Enum):
    """모듈별 구조화된 에러 코드 정의"""

    # ── Sensor (감지부) 에러 ──
    SCREEN_CAPTURE_FAILED = "E_SENSOR_001"   # 화면 캡처 실패
    OCR_FAILED = "E_SENSOR_002"              # OCR 인식 실패
    WINDOW_NOT_FOUND = "E_SENSOR_003"        # 대상 창 찾기 실패

    # ── Brain (두뇌) 에러 ──
    LLM_CONNECTION_FAILED = "E_BRAIN_001"    # LLM 서버 연결 실패
    LLM_TIMEOUT = "E_BRAIN_002"              # LLM 응답 타임아웃
    MAX_STEPS_EXCEEDED = "E_BRAIN_003"       # 최대 스텝 수 초과
    INVALID_TOOL_CALL = "E_BRAIN_004"        # 잘못된 도구 호출

    # ── Embodiment (실행부) 에러 ──
    HID_FAILED = "E_EMB_001"                 # HID 제어 실패
    APP_NOT_FOUND = "E_EMB_002"              # 애플리케이션 찾기 실패
    PERMISSION_DENIED = "E_EMB_003"          # 권한 거부 (Scope 위반)
    OFFICE_COM_ERROR = "E_EMB_004"           # Office COM 인터페이스 에러

    # ── Strategy (전략) 에러 ──
    MCP_CONNECTION_FAILED = "E_STR_001"      # MCP 서버 연결 실패
    TOOL_NOT_FOUND = "E_STR_002"             # 도구 찾기 실패
    TOOL_EXECUTION_FAILED = "E_STR_003"      # 도구 실행 실패

    # ── Safety (안전) 에러 ──
    KILL_SWITCH_ACTIVATED = "E_SAFE_001"     # Kill Switch 발동
    SCOPE_VIOLATION = "E_SAFE_002"           # 스코프 제한 위반
