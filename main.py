"""
main.py — Desktop Pet Agent 시스템 엔트리포인트

CLI 기반으로 사용자 명령을 입력받아 LangGraph 에이전트를 실행하고,
결과를 출력합니다. Kill Switch를 시작하여 우클릭 10회 연타로
프로세스를 안전하게 종료할 수 있습니다.

사용법:
    python main.py --command "Word 문서를 작성해줘"
    python main.py  # 대화형 모드
"""

import argparse
import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가 (모듈 임포트 지원)
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from langchain_core.messages import HumanMessage
from loguru import logger

from brain.graph_builder import build_graph
from config.constants import AgentStatus
from config.settings import get_settings
from embodiment.kill_switch import KillSwitch
from utils.logger import setup_logger


def run_agent(command: str) -> str:
    """에이전트를 실행하여 사용자 명령을 처리합니다.

    Args:
        command: 사용자의 자연어 명령

    Returns:
        에이전트의 최종 응답 메시지
    """
    logger.info("═" * 60)
    logger.info("에이전트 실행 — 명령: '{}'", command)
    logger.info("═" * 60)

    # LangGraph 그래프 빌드
    graph = build_graph()

    # 초기 상태 구성
    initial_state = {
        "messages": [HumanMessage(content=command)],
        "screen_state": None,
        "iteration_count": 0,
        "agent_status": AgentStatus.EXECUTING.value,
        "task_request": {"command": command},
        "action_history": [],
    }

    # 그래프 실행
    try:
        final_state = graph.invoke(initial_state)

        # 최종 응답 추출
        messages = final_state.get("messages", [])
        if messages:
            last_message = messages[-1]
            response = last_message.content if hasattr(last_message, 'content') else str(last_message)
        else:
            response = "에이전트가 응답을 생성하지 못했습니다."

        logger.info("에이전트 실행 완료 — 반복 횟수: {}",
                    final_state.get("iteration_count", 0))
        return response

    except Exception as e:
        logger.error("에이전트 실행 중 오류: {}", str(e))
        return f"에이전트 실행 중 오류가 발생했습니다: {str(e)}"


def interactive_mode(ks: KillSwitch) -> None:
    """대화형 모드 — 사용자가 명령을 입력하면 에이전트가 실행합니다.

    Args:
        ks: Kill Switch 인스턴스
    """
    print("\n" + "═" * 60)
    print("  🐾 Desktop Pet Agent — 대화형 모드")
    print("  명령을 입력하세요 (종료: 'quit' 또는 'exit')")
    print(f"  ⚠️  비상 정지: 마우스 우클릭 10회 빠른 연타")
    print("═" * 60 + "\n")

    while not ks.is_killed:
        try:
            # 사용자 입력 받기
            command = input("📝 명령 > ").strip()

            # 종료 명령 확인
            if command.lower() in ("quit", "exit", "종료", "그만"):
                print("\n👋 에이전트를 종료합니다.")
                break

            # 빈 입력 무시
            if not command:
                continue

            # 에이전트 실행
            response = run_agent(command)

            # 결과 출력
            print(f"\n🤖 응답:\n{response}\n")

        except KeyboardInterrupt:
            print("\n\n👋 Ctrl+C로 종료합니다.")
            break
        except EOFError:
            break


def main():
    """메인 엔트리포인트"""
    # 설정 로드
    settings = get_settings()

    # 로거 초기화
    setup_logger(settings.logs_dir)

    # 데이터 디렉토리 생성
    for dir_path in [settings.data_dir, settings.screenshots_dir, settings.logs_dir]:
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    # CLI 인자 파싱
    parser = argparse.ArgumentParser(
        description="🐾 Desktop Pet Agent — AI 데스크톱 어시스턴트"
    )
    parser.add_argument(
        "--command", "-c",
        type=str,
        default=None,
        help="실행할 명령 (지정하지 않으면 대화형 모드)"
    )
    parser.add_argument(
        "--no-kill-switch",
        action="store_true",
        help="Kill Switch 비활성화 (디버깅용)"
    )
    args = parser.parse_args()

    # Kill Switch 시작
    ks = KillSwitch()
    if not args.no_kill_switch:
        ks.start()
        logger.info(
            "🛑 Kill Switch 활성화 — 마우스 {} {}회 연타({}초) → 종료",
            settings.kill_switch_button,
            settings.kill_switch_click_count,
            settings.kill_switch_time_window,
        )

    try:
        if args.command:
            # 단일 명령 실행 모드
            response = run_agent(args.command)
            print(f"\n🤖 응답:\n{response}")
        else:
            # 대화형 모드
            interactive_mode(ks)

    finally:
        # 정리
        ks.stop()
        logger.info("Desktop Pet Agent 종료")


if __name__ == "__main__":
    main()
