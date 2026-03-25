"""
utils/logger.py — 전역 로깅 설정 모듈

Loguru를 사용하여 콘솔 + 파일 이중 출력 로깅 시스템을 구성합니다.
로그 로테이션, 보존 기간, 레벨별 필터링을 지원합니다.
"""

import sys
from pathlib import Path

from loguru import logger


def setup_logger(log_dir: str = "data/logs") -> logger.__class__:
    """전역 로거를 초기화하고 설정합니다.

    Args:
        log_dir: 로그 파일 저장 디렉토리 경로

    Returns:
        설정된 loguru logger 인스턴스
    """
    # 기존 기본 핸들러 제거 (중복 출력 방지)
    logger.remove()

    # 로그 디렉토리 자동 생성
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    # ── 콘솔 출력 핸들러 ──
    # INFO 이상 레벨을 컬러 포맷으로 stderr에 출력
    logger.add(
        sys.stderr,
        level="INFO",
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        colorize=True,
    )

    # ── 파일 출력 핸들러 ──
    # DEBUG 이상 전체 로그를 파일에 기록 (로테이션 + 보존)
    logger.add(
        str(log_path / "agent_{time:YYYY-MM-DD}.log"),
        level="DEBUG",
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        ),
        rotation="10 MB",      # 10MB마다 새 파일로 로테이션
        retention="7 days",    # 7일 이상 된 로그 파일 자동 삭제
        compression="zip",     # 오래된 로그 파일 압축
        encoding="utf-8",
    )

    logger.info("로거 초기화 완료 — 로그 디렉토리: {}", log_dir)
    return logger


# 모듈 임포트 시 바로 사용할 수 있도록 logger 인스턴스 노출
# 사용 예: from utils.logger import logger
__all__ = ["logger", "setup_logger"]
