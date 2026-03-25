"""
config/settings.py — 전역 설정 및 환경 변수 관리 모듈

PydanticV2 BaseSettings를 사용하여 .env 파일에서 환경 변수를 로드하고,
싱글톤 패턴으로 전역 설정 인스턴스를 관리합니다.
"""

from functools import lru_cache
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    """전역 애플리케이션 설정 — .env 파일에서 자동 로드

    PydanticV2 BaseSettings를 상속하여 DPET_ 접두사의 환경변수를
    자동으로 매핑합니다.
    """

    # ═══════════════════════════════════════════════════════════
    # LLM 설정
    # ═══════════════════════════════════════════════════════════
    vlm_endpoint: str = Field(
        default="http://localhost:11434",
        description="Ollama VLM 서버 엔드포인트 URL"
    )
    vlm_model: str = Field(
        default="qwen3-vl:8b",
        description="사용할 VLM 모델 이름 (OCR/시각 인식 + 툴콜링 지원 모델)"
    )
    llm_temperature: float = Field(
        default=0.1,
        ge=0.0, le=2.0,
        description="LLM 응답 온도 (낮을수록 결정론적)"
    )
    llm_max_tokens: int = Field(
        default=2048,
        ge=128,
        description="LLM 최대 출력 토큰 수"
    )

    # ═══════════════════════════════════════════════════════════
    # Agent 제약 설정
    # ═══════════════════════════════════════════════════════════
    max_agent_steps: int = Field(
        default=15,
        ge=1, le=50,
        description="에이전트 최대 실행 스텝 수 (무한루프 방지)"
    )
    step_timeout_seconds: int = Field(
        default=30,
        ge=5,
        description="단일 도구 실행 타임아웃 (초)"
    )
    total_timeout_seconds: int = Field(
        default=300,
        ge=10,
        description="전체 태스크 타임아웃 (초)"
    )

    # ═══════════════════════════════════════════════════════════
    # Sensor 설정
    # ═══════════════════════════════════════════════════════════
    screen_capture_fps: float = Field(
        default=1.0,
        description="화면 캡처 주기 (FPS)"
    )
    ocr_languages: list[str] = Field(
        default=["ko", "en"],
        description="OCR 인식 대상 언어 목록"
    )
    ocr_confidence_threshold: float = Field(
        default=0.3,
        ge=0.0, le=1.0,
        description="OCR 최소 신뢰도 임계값"
    )

    # ═══════════════════════════════════════════════════════════
    # 안전 설정 (Kill Switch)
    # ═══════════════════════════════════════════════════════════
    kill_switch_click_count: int = Field(
        default=10,
        ge=3, le=20,
        description="Kill Switch 발동에 필요한 클릭 횟수"
    )
    kill_switch_time_window: float = Field(
        default=1.5,
        ge=0.5, le=5.0,
        description="Kill Switch 클릭 감지 시간 윈도우 (초)"
    )
    kill_switch_button: str = Field(
        default="right",
        description="Kill Switch 감지 마우스 버튼 ('left' 또는 'right')"
    )
    allowed_apps: list[str] = Field(
        default=[],
        description="허용된 애플리케이션 목록 (빈 리스트 = 제한 없음)"
    )
    allowed_directories: list[str] = Field(
        default=[],
        description="허용된 디렉토리 목록 (빈 리스트 = 제한 없음)"
    )
    dangerous_tools_enabled: bool = Field(
        default=False,
        description="위험 도구(파일 삭제/이동) 활성화 여부"
    )

    # ═══════════════════════════════════════════════════════════
    # MCP 서버 설정
    # ═══════════════════════════════════════════════════════════
    mcp_servers: list[dict] = Field(
        default=[],
        description="MCP 서버 연결 설정 목록 (MCPServerConfig 형태)"
    )

    # ═══════════════════════════════════════════════════════════
    # 경로 설정
    # ═══════════════════════════════════════════════════════════
    data_dir: str = Field(default="data", description="데이터 루트 디렉토리")
    screenshots_dir: str = Field(default="data/screenshots", description="스크린샷 저장 경로")
    logs_dir: str = Field(default="data/logs", description="로그 파일 저장 경로")
    db_path: str = Field(default="data/desktop_pet.db", description="SQLite DB 파일 경로")
    results_dir: str = Field(default="data/results", description="생성된 작업물 저장 경로")

    # ═══════════════════════════════════════════════════════════
    # Pydantic Settings 설정 (V2 방식)
    # ═══════════════════════════════════════════════════════════
    model_config = SettingsConfigDict(
        env_file=".env",           # .env 파일에서 환경변수 로드
        env_prefix="DPET_",        # 환경변수 접두사
        env_file_encoding="utf-8", # 파일 인코딩
        case_sensitive=False,      # 대/소문자 무시
        extra="ignore",            # 알 수 없는 환경변수 무시
    )


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    """전역 설정 싱글톤 인스턴스를 반환합니다.

    lru_cache를 사용하여 최초 호출 시에만 인스턴스를 생성하고,
    이후에는 캐시된 인스턴스를 반환합니다.

    Returns:
        AppSettings: 전역 설정 인스턴스
    """
    return AppSettings()
