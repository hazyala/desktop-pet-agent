"""
embodiment/kill_switch.py — 비상 정지 시스템 모듈

pynput을 사용하여 마우스 우클릭 10회 빠른 연타를 감지하고,
프로세스를 안전하게 종료하는 하드웨어 킬 스위치를 구현합니다.

메커니즘:
    - Hard Kill: 마우스 우클릭 10회 연타 (1.5초 이내) → 프로세스 종료
    - Soft Pause: (향후 확장) 단축키 → 일시 정지/재개

Kill Switch는 독립 스레드에서 상시 감시하며,
에이전트 메인 루프와 독립적으로 동작합니다.
"""

import os
import sys
import time
import threading
from collections import deque
from typing import Optional

from pynput import mouse
from loguru import logger

from config.settings import get_settings


class KillSwitch:
    """마우스 우클릭 연타 기반 비상 정지 시스템

    pynput.mouse.Listener를 사용하여 백그라운드에서 마우스 클릭을
    감시하고, 설정된 횟수만큼 빠르게 연타하면 kill_event를 발동합니다.

    Attributes:
        kill_event: 비상 정지 이벤트 (threading.Event)
        pause_event: 일시 정지 이벤트 (threading.Event, 향후 확장)
    """

    def __init__(
        self,
        click_count: Optional[int] = None,
        time_window: Optional[float] = None,
        button: Optional[str] = None,
    ):
        """Kill Switch를 초기화합니다.

        Args:
            click_count: Kill Switch 발동에 필요한 클릭 횟수 (기본값: 설정에서 로드)
            time_window: 클릭 감지 시간 윈도우 (초) (기본값: 설정에서 로드)
            button: 감지할 마우스 버튼 ('left' 또는 'right', 기본값: 설정에서 로드)
        """
        # 설정에서 기본값 로드
        settings = get_settings()
        self._click_count = click_count or settings.kill_switch_click_count
        self._time_window = time_window or settings.kill_switch_time_window
        self._button = button or settings.kill_switch_button

        # ── 이벤트 플래그 ──
        self.kill_event = threading.Event()     # 비상 정지 이벤트
        self.pause_event = threading.Event()    # 일시 정지 이벤트 (향후 확장)

        # ── 클릭 타임스탬프 큐 ──
        # 최대 click_count만큼의 최근 클릭 시각을 저장
        self._click_timestamps: deque[float] = deque(maxlen=self._click_count)

        # ── 마우스 리스너 ──
        self._listener: Optional[mouse.Listener] = None
        self._running = False

        logger.info(
            "Kill Switch 초기화 — 버튼: {}, 횟수: {}, 시간 윈도우: {}초",
            self._button, self._click_count, self._time_window
        )

    def _on_click(
        self,
        x: int,
        y: int,
        button: mouse.Button,
        pressed: bool,
    ) -> None:
        """마우스 클릭 이벤트 핸들러

        지정된 버튼의 클릭(눌림) 이벤트만 감지하여 타임스탬프를 기록합니다.
        설정된 횟수만큼 시간 윈도우 내에 연타하면 kill_event를 발동합니다.

        Args:
            x: 클릭 X 좌표
            y: 클릭 Y 좌표
            button: 클릭된 마우스 버튼
            pressed: True=버튼 눌림, False=버튼 뗌
        """
        # 버튼 눌림 이벤트만 처리 (뗌 이벤트 무시)
        if not pressed:
            return

        # 설정된 버튼과 일치하는지 확인
        target_button = (
            mouse.Button.right if self._button == "right"
            else mouse.Button.left
        )
        if button != target_button:
            return

        # 현재 시각을 타임스탬프 큐에 추가
        current_time = time.time()
        self._click_timestamps.append(current_time)

        # 큐가 가득 찼을 때 (click_count만큼의 클릭이 기록됨)
        if len(self._click_timestamps) == self._click_count:
            # 가장 오래된 클릭과 가장 최근 클릭의 시간 차이 계산
            time_diff = self._click_timestamps[-1] - self._click_timestamps[0]

            # 시간 윈도우 내에 모든 클릭이 발생했다면 Kill Switch 발동
            if time_diff <= self._time_window:
                logger.critical(
                    "🛑 Kill Switch 발동! — {}클릭 {:.2f}초 이내 감지",
                    self._click_count, time_diff
                )
                self.kill_event.set()

                # 타임스탬프 큐 초기화 (중복 발동 방지)
                self._click_timestamps.clear()

                # 프로세스 강제 종료
                self._force_exit()

    def _force_exit(self) -> None:
        """프로세스를 강제 종료합니다.

        리스너를 정지한 후 os._exit()으로 즉시 프로세스를 종료합니다.
        SystemExit 예외와 달리 try-except로 잡을 수 없어 확실한 종료를 보장합니다.
        """
        logger.critical("🛑 프로세스 강제 종료 중...")
        self.stop()
        os._exit(1)

    def start(self) -> None:
        """Kill Switch 감시를 시작합니다.

        pynput 마우스 리스너를 백그라운드 스레드에서 실행합니다.
        """
        if self._running:
            logger.warning("Kill Switch가 이미 실행 중입니다.")
            return

        self._running = True
        self._listener = mouse.Listener(on_click=self._on_click)
        self._listener.daemon = True  # 메인 스레드 종료 시 함께 종료
        self._listener.start()

        logger.info(
            "✅ Kill Switch 감시 시작 — 마우스 {} {}회 연타({}초 이내) → 프로세스 종료",
            self._button, self._click_count, self._time_window
        )

    def stop(self) -> None:
        """Kill Switch 감시를 중지합니다."""
        if self._listener:
            self._listener.stop()
            self._listener = None
        self._running = False
        logger.info("Kill Switch 감시 중지")

    def wait_for_kill(self, timeout: Optional[float] = None) -> bool:
        """Kill Switch 발동을 대기합니다.

        Args:
            timeout: 대기 타임아웃 (초). None이면 무한 대기.

        Returns:
            True: Kill Switch가 발동됨
            False: 타임아웃으로 대기 중단
        """
        return self.kill_event.wait(timeout=timeout)

    @property
    def is_killed(self) -> bool:
        """Kill Switch가 발동되었는지 확인합니다."""
        return self.kill_event.is_set()

    @property
    def is_paused(self) -> bool:
        """일시 정지 상태인지 확인합니다. (향후 확장)"""
        return self.pause_event.is_set()
