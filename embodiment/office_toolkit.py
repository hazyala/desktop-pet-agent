"""
embodiment/office_toolkit.py — Word 문서 자동화 모듈 (COM 인터페이스)

pywin32 COM을 사용하여 Microsoft Word 문서의 작성, 읽기, 수정, 삭제를
수행합니다. Visible=True로 설정하여 사용자에게 실시간으로 편집 과정을 보여줍니다.

핵심 설계:
    ★ COM(pywin32) 우선 전략 ★
    - 1차: win32com.client.Dispatch("Word.Application")
    - 2차(폴백): python-docx (향후 구현, Office 미설치 환경 대응)
"""

import os
import time
from pathlib import Path
from typing import Optional

import pythoncom
import win32com.client
from loguru import logger


class OfficeToolkit:
    """pywin32 COM 기반 Word 문서 자동화 도구

    Word.Application COM 객체를 Visible=True로 생성하여,
    사용자가 문서 편집 과정을 실시간으로 확인할 수 있습니다.

    사용 예:
        toolkit = OfficeToolkit()
        path = toolkit.create_document("d:/docs/report.docx", "보고서", "내용...")
        content = toolkit.read_document(path)
        toolkit.append_paragraph(path, "추가 문단입니다.")
        toolkit.find_replace(path, "이전텍스트", "새텍스트")
        toolkit.delete_document(path)
    """

    def __init__(self, visible: bool = True):
        """OfficeToolkit을 초기화합니다.

        Args:
            visible: Word 애플리케이션을 화면에 표시할지 여부 (기본값: True)
        """
        self._visible = visible
        self._word_app: Optional[object] = None
        logger.info("OfficeToolkit 초기화 — Visible: {}", visible)

    def _get_word_app(self) -> object:
        """Word.Application COM 객체를 가져오거나 새로 생성합니다.

        COM 초기화(CoInitialize)를 수행하고, Word 애플리케이션을 실행합니다.
        기존에 생성된 인스턴스가 있으면 재사용합니다.

        Returns:
            Word.Application COM 객체
        """
        try:
            # COM 라이브러리 초기화 (스레드별 필수)
            pythoncom.CoInitialize()

            if self._word_app is None:
                logger.info("Word.Application COM 객체 생성 중...")
                self._word_app = win32com.client.Dispatch("Word.Application")
                self._word_app.Visible = self._visible  # 화면 표시 여부 설정
                logger.info("✅ Word.Application 생성 완료 — Visible: {}", self._visible)

            return self._word_app

        except Exception as e:
            logger.error("Word.Application 생성 실패: {}", str(e))
            raise RuntimeError(f"Word COM 초기화 실패: {e}")

    def create_document(
        self,
        file_path: str,
        title: str,
        content: str,
        save_format: int = 16,  # wdFormatDocumentDefault (docx)
    ) -> str:
        """새 Word 문서를 생성하고 저장합니다.

        Args:
            file_path: 저장할 파일 경로 (절대 경로 권장)
            title: 문서 제목 (첫 번째 문단에 삽입)
            content: 문서 본문 내용
            save_format: 저장 형식 (기본값: 16 = docx)

        Returns:
            저장된 파일의 절대 경로
        """
        word = self._get_word_app()

        try:
            # 저장 디렉토리 자동 생성
            abs_path = str(Path(file_path).resolve())
            Path(abs_path).parent.mkdir(parents=True, exist_ok=True)

            logger.info("Word 문서 생성 중: {}", abs_path)

            # 새 문서 생성
            doc = word.Documents.Add()

            # 제목 삽입 (스타일: 제목 1)
            title_range = doc.Range(0, 0)
            title_range.Text = title + "\n"
            try:
                title_range.Style = "제목 1"
            except Exception:
                # 영문 Word의 경우 스타일명이 다를 수 있음
                try:
                    title_range.Style = "Heading 1"
                except Exception:
                    logger.warning("제목 스타일 적용 실패 — 기본 스타일 사용")

            # 본문 내용 삽입
            content_range = doc.Range(doc.Content.End - 1, doc.Content.End - 1)
            content_range.Text = content

            # 문서 저장 (docx 형식)
            doc.SaveAs2(abs_path, FileFormat=save_format)
            logger.info("✅ Word 문서 저장 완료: {}", abs_path)

            return abs_path

        except Exception as e:
            logger.error("Word 문서 생성 실패: {}", str(e))
            raise

    def read_document(self, file_path: str) -> str:
        """Word 문서의 전체 텍스트 내용을 읽습니다.

        Args:
            file_path: 읽을 문서 파일 경로

        Returns:
            문서의 전체 텍스트 내용
        """
        word = self._get_word_app()

        try:
            abs_path = str(Path(file_path).resolve())
            logger.info("Word 문서 읽기: {}", abs_path)

            # 문서 열기 (읽기 전용)
            doc = word.Documents.Open(abs_path, ReadOnly=True)
            text = doc.Content.Text
            doc.Close(SaveChanges=False)

            logger.info("✅ Word 문서 읽기 완료 — 글자 수: {}", len(text))
            return text

        except Exception as e:
            logger.error("Word 문서 읽기 실패: {}", str(e))
            raise

    def append_paragraph(
        self,
        file_path: str,
        text: str,
        style: Optional[str] = None,
    ) -> bool:
        """Word 문서에 새 문단을 추가합니다.

        Args:
            file_path: 대상 문서 파일 경로
            text: 추가할 텍스트
            style: 적용할 스타일명 (예: "제목 2", "본문", None=기본)

        Returns:
            성공 여부
        """
        word = self._get_word_app()

        try:
            abs_path = str(Path(file_path).resolve())
            logger.info("Word 문서 문단 추가: {} → '{}'", abs_path, text[:50])

            # 문서 열기 (편집 모드)
            doc = word.Documents.Open(abs_path)

            # 문서 끝에 새 문단 추가
            end_range = doc.Range(doc.Content.End - 1, doc.Content.End - 1)
            end_range.InsertParagraphAfter()
            end_range = doc.Range(doc.Content.End - 1, doc.Content.End - 1)
            end_range.Text = text

            # 스타일 적용 (지정된 경우)
            if style:
                try:
                    end_range.Style = style
                except Exception:
                    logger.warning("스타일 '{}' 적용 실패 — 기본 스타일 유지", style)

            # 저장 및 닫기
            doc.Save()
            doc.Close()

            logger.info("✅ 문단 추가 완료")
            return True

        except Exception as e:
            logger.error("Word 문단 추가 실패: {}", str(e))
            return False

    def find_replace(
        self,
        file_path: str,
        find_text: str,
        replace_text: str,
    ) -> int:
        """Word 문서에서 텍스트를 찾아 바꿉니다.

        Args:
            file_path: 대상 문서 파일 경로
            find_text: 찾을 텍스트
            replace_text: 바꿀 텍스트

        Returns:
            치환된 횟수 (COM에서 정확한 횟수를 반환하지 않으므로 0 또는 1)
        """
        word = self._get_word_app()

        try:
            abs_path = str(Path(file_path).resolve())
            logger.info("Word 찾아 바꾸기: '{}' → '{}'", find_text, replace_text)

            # 문서 열기
            doc = word.Documents.Open(abs_path)

            # 찾기/바꾸기 실행
            find_obj = doc.Content.Find
            replaced = find_obj.Execute(
                FindText=find_text,
                ReplaceWith=replace_text,
                Replace=2,  # wdReplaceAll = 2
                Forward=True,
                Wrap=1,     # wdFindContinue = 1
            )

            # 저장 및 닫기
            doc.Save()
            doc.Close()

            result_count = 1 if replaced else 0
            logger.info("✅ 찾아 바꾸기 완료 — 치환 여부: {}", replaced)
            return result_count

        except Exception as e:
            logger.error("Word 찾아 바꾸기 실패: {}", str(e))
            return 0

    def edit_document(
        self,
        file_path: str,
        new_content: str,
    ) -> bool:
        """Word 문서의 전체 내용을 새 내용으로 교체합니다.

        Args:
            file_path: 대상 문서 파일 경로
            new_content: 교체할 새 내용

        Returns:
            성공 여부
        """
        word = self._get_word_app()

        try:
            abs_path = str(Path(file_path).resolve())
            logger.info("Word 문서 내용 교체: {}", abs_path)

            # 문서 열기
            doc = word.Documents.Open(abs_path)

            # 전체 내용 교체
            doc.Content.Text = new_content

            # 저장 및 닫기
            doc.Save()
            doc.Close()

            logger.info("✅ 문서 내용 교체 완료")
            return True

        except Exception as e:
            logger.error("Word 문서 내용 교체 실패: {}", str(e))
            return False

    def delete_document(self, file_path: str) -> bool:
        """Word 문서 파일을 삭제합니다.

        열려있는 문서라면 먼저 닫은 후 파일을 삭제합니다.

        Args:
            file_path: 삭제할 파일 경로

        Returns:
            성공 여부
        """
        try:
            abs_path = str(Path(file_path).resolve())
            logger.info("Word 문서 삭제: {}", abs_path)

            # Word에서 해당 문서가 열려있으면 닫기
            word = self._get_word_app()
            for doc in word.Documents:
                if str(Path(doc.FullName).resolve()) == abs_path:
                    doc.Close(SaveChanges=False)
                    logger.info("열려있던 문서 닫기 완료: {}", abs_path)
                    break

            # 파일 시스템에서 삭제
            if os.path.exists(abs_path):
                os.remove(abs_path)
                logger.info("✅ 파일 삭제 완료: {}", abs_path)
                return True
            else:
                logger.warning("파일이 존재하지 않습니다: {}", abs_path)
                return False

        except Exception as e:
            logger.error("Word 문서 삭제 실패: {}", str(e))
            return False

    def quit(self) -> None:
        """Word 애플리케이션을 종료합니다.

        열려있는 모든 문서를 저장 없이 닫고 Word를 종료합니다.
        COM 리소스를 정리합니다.
        """
        try:
            if self._word_app:
                # 열린 문서 모두 닫기
                for doc in self._word_app.Documents:
                    doc.Close(SaveChanges=False)

                # Word 종료
                self._word_app.Quit()
                self._word_app = None
                logger.info("✅ Word.Application 종료 완료")

            # COM 라이브러리 해제
            pythoncom.CoUninitialize()

        except Exception as e:
            logger.error("Word.Application 종료 실패: {}", str(e))
            self._word_app = None

    def __del__(self):
        """소멸자 — Word 애플리케이션이 남아있으면 정리 시도"""
        try:
            self.quit()
        except Exception:
            pass
