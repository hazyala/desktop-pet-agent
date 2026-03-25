"""
strategy/local_tools.py — 로컬 LangChain 도구 정의 모듈

1주차: Word 문서 CRUD 도구 + 유틸리티 도구를 @tool 데코레이터로 정의합니다.
각 도구는 embodiment 모듈에 실행을 위임합니다.
"""

import time
from typing import Optional

from langchain_core.tools import tool
from loguru import logger

from config.constants import ToolCategory, ToolRiskLevel
from config.types_dto import ToolInfo
from embodiment.office_toolkit import OfficeToolkit
from strategy.tool_registry import ToolRegistry


# ═══════════════════════════════════════════════════════════════
# Word 문서 CRUD 도구
# ═══════════════════════════════════════════════════════════════

@tool
def create_word_doc(
    file_path: str,
    title: str,
    content: str,
) -> str:
    """Word 문서를 새로 생성하고 저장합니다.

    Args:
        file_path: 저장할 파일의 절대 경로 (반드시 'D:/Desktop_Pet/data/results/' 하위에 저장하세요. 예: 'D:/Desktop_Pet/data/results/report.docx')
        title: 문서 제목
        content: 문서 본문 내용

    Returns:
        생성된 파일의 절대 경로
    """
    logger.info("도구 실행: create_word_doc — {}", file_path)
    toolkit = OfficeToolkit(visible=True)
    try:
        result = toolkit.create_document(file_path, title, content)
        return f"Word 문서 생성 완료: {result}"
    except Exception as e:
        return f"Word 문서 생성 실패: {str(e)}"


@tool
def read_word_doc(file_path: str) -> str:
    """Word 문서의 전체 텍스트 내용을 읽습니다.

    Args:
        file_path: 읽을 문서 파일의 절대 경로 (예: 'D:/Desktop_Pet/data/results/report.docx')

    Returns:
        문서의 전체 텍스트 내용
    """
    logger.info("도구 실행: read_word_doc — {}", file_path)
    toolkit = OfficeToolkit(visible=True)
    try:
        content = toolkit.read_document(file_path)
        return f"문서 내용:\n{content}"
    except Exception as e:
        return f"Word 문서 읽기 실패: {str(e)}"


@tool
def edit_word_doc(
    file_path: str,
    new_content: str,
) -> str:
    """Word 문서의 전체 내용을 새 내용으로 교체합니다.

    Args:
        file_path: 대상 문서 파일의 절대 경로 (예: 'D:/Desktop_Pet/data/results/report.docx')
        new_content: 교체할 새 내용

    Returns:
        작업 결과 메시지
    """
    logger.info("도구 실행: edit_word_doc — {}", file_path)
    toolkit = OfficeToolkit(visible=True)
    try:
        success = toolkit.edit_document(file_path, new_content)
        if success:
            return f"Word 문서 수정 완료: {file_path}"
        return "Word 문서 수정 실패"
    except Exception as e:
        return f"Word 문서 수정 실패: {str(e)}"


@tool
def append_word_paragraph(
    file_path: str,
    text: str,
    style: Optional[str] = None,
) -> str:
    """Word 문서에 새 문단을 추가합니다.

    Args:
        file_path: 대상 문서 파일의 절대 경로 (예: 'D:/Desktop_Pet/data/results/report.docx')
        text: 추가할 텍스트
        style: 적용할 스타일 (예: '제목 2', '본문')

    Returns:
        작업 결과 메시지
    """
    logger.info("도구 실행: append_word_paragraph — {}", file_path)
    toolkit = OfficeToolkit(visible=True)
    try:
        success = toolkit.append_paragraph(file_path, text, style)
        if success:
            return f"문단 추가 완료: '{text[:50]}...'"
        return "문단 추가 실패"
    except Exception as e:
        return f"문단 추가 실패: {str(e)}"


@tool
def delete_word_doc(file_path: str) -> str:
    """Word 문서 파일을 삭제합니다.

    Args:
        file_path: 삭제할 파일의 절대 경로 (예: 'D:/Desktop_Pet/data/results/report.docx')

    Returns:
        작업 결과 메시지
    """
    logger.info("도구 실행: delete_word_doc — {}", file_path)
    toolkit = OfficeToolkit(visible=True)
    try:
        success = toolkit.delete_document(file_path)
        if success:
            return f"Word 문서 삭제 완료: {file_path}"
        return f"Word 문서 삭제 실패: 파일이 존재하지 않습니다"
    except Exception as e:
        return f"Word 문서 삭제 실패: {str(e)}"


@tool
def find_replace_word(
    file_path: str,
    find_text: str,
    replace_text: str,
) -> str:
    """Word 문서에서 텍스트를 찾아 바꿉니다.

    Args:
        file_path: 대상 문서 파일의 절대 경로 (예: 'D:/Desktop_Pet/data/results/report.docx')
        find_text: 찾을 텍스트
        replace_text: 바꿀 텍스트

    Returns:
        작업 결과 메시지
    """
    logger.info("도구 실행: find_replace_word — {} → {}", find_text, replace_text)
    toolkit = OfficeToolkit(visible=True)
    try:
        count = toolkit.find_replace(file_path, find_text, replace_text)
        return f"찾아 바꾸기 완료: '{find_text}' → '{replace_text}' ({count}건)"
    except Exception as e:
        return f"찾아 바꾸기 실패: {str(e)}"


# ═══════════════════════════════════════════════════════════════
# 유틸리티 도구
# ═══════════════════════════════════════════════════════════════

@tool
def wait_seconds(seconds: float) -> str:
    """지정된 시간(초)만큼 대기합니다.

    Args:
        seconds: 대기 시간 (초, 최대 30초)

    Returns:
        대기 완료 메시지
    """
    # 안전 제한: 최대 30초
    wait_time = min(seconds, 30.0)
    logger.info("도구 실행: wait_seconds — {}초 대기", wait_time)
    time.sleep(wait_time)
    return f"{wait_time}초 대기 완료"


# ═══════════════════════════════════════════════════════════════
# 도구 등록 함수
# ═══════════════════════════════════════════════════════════════

def register_local_tools(registry: ToolRegistry) -> None:
    """1주차 로컬 도구를 레지스트리에 등록합니다.

    Args:
        registry: 도구 레지스트리 인스턴스
    """
    # Word CRUD 도구 목록 (도구 인스턴스, 메타데이터)
    tools_with_info: list[tuple] = [
        (
            create_word_doc,
            ToolInfo(
                name="create_word_doc",
                description="Word 문서를 새로 생성하고 저장합니다",
                category=ToolCategory.OFFICE,
                risk_level=ToolRiskLevel.MEDIUM,
                source="local",
            ),
        ),
        (
            read_word_doc,
            ToolInfo(
                name="read_word_doc",
                description="Word 문서의 전체 텍스트 내용을 읽습니다",
                category=ToolCategory.OFFICE,
                risk_level=ToolRiskLevel.SAFE,
                source="local",
            ),
        ),
        (
            edit_word_doc,
            ToolInfo(
                name="edit_word_doc",
                description="Word 문서의 전체 내용을 새 내용으로 교체합니다",
                category=ToolCategory.OFFICE,
                risk_level=ToolRiskLevel.MEDIUM,
                source="local",
            ),
        ),
        (
            append_word_paragraph,
            ToolInfo(
                name="append_word_paragraph",
                description="Word 문서에 새 문단을 추가합니다",
                category=ToolCategory.OFFICE,
                risk_level=ToolRiskLevel.MEDIUM,
                source="local",
            ),
        ),
        (
            delete_word_doc,
            ToolInfo(
                name="delete_word_doc",
                description="Word 문서 파일을 삭제합니다",
                category=ToolCategory.OFFICE,
                risk_level=ToolRiskLevel.HIGH,
                source="local",
            ),
        ),
        (
            find_replace_word,
            ToolInfo(
                name="find_replace_word",
                description="Word 문서에서 텍스트를 찾아 바꿉니다",
                category=ToolCategory.OFFICE,
                risk_level=ToolRiskLevel.MEDIUM,
                source="local",
            ),
        ),
        (
            wait_seconds,
            ToolInfo(
                name="wait_seconds",
                description="지정된 시간(초)만큼 대기합니다",
                category=ToolCategory.UTIL,
                risk_level=ToolRiskLevel.SAFE,
                source="local",
            ),
        ),
    ]

    # 레지스트리에 등록
    registry.register_tools(tools_with_info)
    logger.info("[성공] 1주차 로컬 도구 {}개 등록 완료", len(tools_with_info))
