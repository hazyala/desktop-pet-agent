# Desktop Pet Agent — Development Plan (개발 계획서)

> **버전**: 1.0  
> **최종 수정**: 2026-03-23  
---

## 1. 개발 전략 개요

### 1-1. 단계별 접근 (Phase 분리)

| Phase | 목표 | 핵심 산출물 |
|-------|------|-----------|
| **Phase 1** | 코어 에이전트 파이프라인 | 화면 인식 → LangGraph 추론 → HID/API 실행 |
| **Phase 2** | UI 및 확장 기능 | PySide6 펫 윈도우, STT/TTS, 외부 DB |

### 1-2. Phase 1 핵심 원칙

1. **에이전트 코어 우선**: GUI 없이 CLI/스크립트로 명령 입력 → 실행 → 결과 확인
2. **Bottom-Up 구축**: 하위 모듈(config, sensor, embodiment) → 상위 모듈(brain, strategy)
3. **하드코딩 우선**: LLM 통합 전에 하드코딩으로 전체 파이프라인 동작 검증
4. **안전 최우선**: Kill Switch는 다른 모든 기능보다 먼저 구현 및 테스트

---

## 2. Phase 1 스프린트 계획

### Sprint 1 — 기반 구축 + 하드코딩 파이프라인

> **목표**: LLM 없이 하드코딩된 시나리오로 Sensor → Embodiment 경로 검증

| # | 작업 | 구현 파일 | 산출물 / 완료 기준 |
|---|------|----------|-------------------|
| 1 | 프로젝트 뼈대 생성 | `environment.yml`, 전체 폴더 구조 | Conda 환경 활성화 + import 에러 없음 |
| 2 | 전역 설정 모듈 | `config/settings.py`, `config/constants.py` | `.env` 로드 → `AppSettings` 인스턴스 생성 확인 |
| 3 | DTO 정의 | `config/types_dto.py` | 모든 Pydantic 모델 import + 직렬화/역직렬화 테스트 |
| 4 | 로깅 시스템 | `utils/logger.py` | 콘솔 + 파일 로그 이중 출력 확인 |
| 5 | 화면 캡처 | `sensor/screen_grabber.py` | 스크린샷 캡처 → PIL Image 반환 + 파일 저장 |
| 6 | OCR 엔진 | `sensor/ocr_engine.py` | 스크린샷 → `OCRResult` DTO (한/영 텍스트 + 좌표) |
| 7 | OS 모니터 | `sensor/os_monitor.py` | `ActiveWindowInfo` + `MouseState` 반환 |
| 8 | HID 컨트롤러 | `embodiment/hid_controller.py` | 마우스 이동/클릭, 텍스트 입력 (한글 포함) 동작 |
| 9 | **Kill Switch** | `embodiment/kill_switch.py` | 좌클릭 6연타 → 이벤트 감지, 독립 스레드 동작 |
| 10 | **하드코딩 E2E** | `tests/test_integration.py` | "메모장 열기 → 텍스트 입력" 시나리오 통과 (LLM 없이) |

#### Sprint 1 검증 방법

```bash
# 1. 환경 설정 확인
conda activate desktop-pet
python -c "from config.settings import get_settings; print(get_settings())"

# 2. DTO 검증
python -c "from config.types_dto import ScreenState, TaskRequest; print('DTO OK')"

# 3. 센서 검증 (스크린샷 + OCR)
python -c "
from sensor.screen_grabber import ScreenGrabber
from sensor.ocr_engine import OCREngine
sg = ScreenGrabber()
img = sg.capture()
ocr = OCREngine()
result = ocr.recognize(img)
print(f'블록 수: {result.block_count}, 전문: {result.full_text[:100]}')
"

# 4. HID 검증 (메모장 열기 + 입력)
python tests/test_integration.py --scenario notepad_typing

# 5. Kill Switch 검증
python -c "
from embodiment.kill_switch import KillSwitch
ks = KillSwitch()
ks.start()
print('좌클릭 6연타로 종료 테스트...')
ks.wait_for_kill()
print('Kill Switch 감지 성공!')
"
```

---

### Sprint 2 — Brain (LangGraph) 통합 + 도구 레지스트리

> **목표**: LangGraph 기반 순환 루프로 LLM이 도구를 선택하고 실행하는 구조 완성

| # | 작업 | 구현 파일 | 산출물 / 완료 기준 |
|---|------|----------|-------------------|
| 1 | LangGraph 상태 정의 | `brain/graph_state.py` | `AgentGraphState` TypedDict 정의 |
| 2 | 프롬프트 관리 | `brain/prompts.py` | 시스템 프롬프트 + 화면 컨텍스트 템플릿 |
| 3 | Reasoning 노드 | `brain/nodes/reasoning_node.py` | ChatOllama ↔ LLM 호출 + AIMessage 반환 |
| 4 | Tool 노드 | `brain/nodes/tool_node.py` | tool_call 파싱 → 도구 실행 → ToolMessage 반환 |
| 5 | 그래프 빌더 | `brain/graph_builder.py` | StateGraph 구성 + 조건부 엣지 + compile() |
| 6 | 로컬 도구 정의 | `strategy/local_tools.py` | 21개 MVP 도구 @tool 정의 (Section 4-5 참조) |
| 7 | 도구 레지스트리 | `strategy/tool_registry.py` | 통합 레지스트리: 등록/검색/활성화 |
| 8 | Blackboard | `state/blackboard.py` | thread-safe 상태 보관 + 갱신 |
| 9 | Memory DB | `state/memory_db.py` | SQLite 테이블 생성 + 로그 저장/조회 |
| 10 | **LLM E2E 테스트** | — | "메모장에 '안녕하세요' 입력해줘" → LLM 주도 실행 성공 |

#### Sprint 2 검증 방법

```bash
# 1. LangGraph 그래프 구조 확인
python -c "
from brain.graph_builder import build_graph
graph = build_graph()
print(graph.get_graph().draw_ascii())
"

# 2. LLM 연결 확인
python -c "
from langchain_ollama import ChatOllama
llm = ChatOllama(model='gemma3:27b', base_url='http://your-ollama-host:11434')
resp = llm.invoke('Hello, respond in one word.')
print(resp.content)
"

# 3. 도구 레지스트리 확인
python -c "
from strategy.tool_registry import ToolRegistry
reg = ToolRegistry()
tools = reg.get_all_tools()
print(f'등록된 도구 수: {len(tools)}')
for t in tools: print(f'  - {t.name}')
"

# 4. LLM 주도 E2E (메모장 시나리오)
python main.py --command "메모장을 열고 '안녕하세요'를 입력해줘"
```

---

### Sprint 3 — OS/Office 도구 + MCP 통합

> **목표**: OS 제어, Office 자동화, MCP 클라이언트까지 포함한 완전한 도구 생태계 구축

| # | 작업 | 구현 파일 | 산출물 / 완료 기준 |
|---|------|----------|-------------------|
| 1 | OS 툴킷 | `embodiment/os_toolkit.py` | 앱 실행, 창 전환, 클립보드, 파일 I/O |
| 2 | Office 툴킷 (COM 우선) | `embodiment/office_toolkit.py` | COM(pywin32) 기반 Excel/Word 실시간 제어 + openpyxl/python-docx 폴백 |
| 3 | OS 도구 연결 | `strategy/local_tools.py` 추가 | open_app, switch_window, list_directory 등 |
| 4 | Office 도구 연결 | `strategy/local_tools.py` 추가 | create_excel, read_excel, create_word_doc 등 |
| 5 | MCP 클라이언트 (langchain-mcp-adapters) | `strategy/mcp_client.py` | MultiServerMCPClient 기반 MCP 서버 연결 + LangChain Tool 자동 변환 |
| 6 | MCP 레지스트리 통합 | `strategy/tool_registry.py` 수정 | MCP 도구를 통합 레지스트리에 동적 등록 |
| 7 | Scope 제한 구현 | `embodiment/os_toolkit.py` | 허용 폴더/앱 화이트리스트 적용 |
| 8 | Soft Pause 구현 | `embodiment/kill_switch.py` 확장 | pause_event + 재개 로직 |
| 9 | **Office E2E** | — | "실적 데이터를 엑셀로 정리해줘" → Excel 파일 생성 |
| 10 | **통합 E2E** | — | "카카오톡에서 OO에게 메시지 보내줘" → 전체 파이프라인 |

#### Sprint 3 검증 방법

```bash
# 1. Office 도구 단위 테스트
python -c "
from embodiment.office_toolkit import OfficeToolkit
ot = OfficeToolkit()
ot.create_workbook('data/test.xlsx', {'Sheet1': [['이름','점수'],['Kim',95],['Lee',88]]})
data = ot.read_workbook('data/test.xlsx')
print(data)
"

# 2. MCP 클라이언트 연결 확인 (MCP 서버 구동 필요)
python -c "
from strategy.mcp_client import MCPClient
client = MCPClient()
# 설정된 MCP 서버가 있는 경우에만 동작
tools = client.get_available_tools()
print(f'MCP 도구 수: {len(tools)}')
"

# 3. 통합 E2E
python main.py --command "D:/Documents 폴더의 파일 목록을 보여줘"
python main.py --command "새 엑셀 파일을 만들고 1월~3월 매출 데이터를 정리해줘"
```

---

### Sprint 4 — 안정화 + 문서화 + 성능 최적화

> **목표**: 에러 핸들링 강화, 테스트 완비, Phase 1 최종 릴리스

| # | 작업 | 산출물 / 완료 기준 |
|---|------|-------------------|
| 1 | 에러 핸들링 강화 | 모든 모듈에 try-except + ErrorCode 기반 구조화된 에러 |
| 2 | 단위 테스트 작성 | `test_sensor.py`, `test_brain.py`, `test_embodiment.py` |
| 3 | 통합 테스트 보강 | `test_integration.py`: 5개 이상의 시나리오 커버 |
| 4 | 로깅 정비 | 모든 주요 동작에 적절한 로그 레벨/메시지 |
| 5 | LLM 프롬프트 튜닝 | 실패 케이스 분석 → 프롬프트 개선 |
| 6 | 성능 최적화 | OCR 캐싱, 스크린샷 리사이징, LLM 응답 시간 모니터링 |
| 7 | `README.md` 작성 | 설치법, 실행법, 사용 예시, 안전 주의사항 |
| 8 | `environment.yml` 확정 | 실제 사용된 라이브러리 + 정확한 버전 핀 |
| 9 | `.env.example` 작성 | 모든 환경변수 키 + 설명 주석 |

---

## 3. Phase 2 계획 (요약)

> Phase 1 완료 후 착수. 상세 계획은 Phase 1 완료 시점에 수립합니다.

### Sprint 5 — PySide6 UI

| 작업 | 설명 |
|------|------|
| 투명 윈도우 | `gui/main_window.py`: 항상 위에 표시되는 투명 펫 캐릭터 |
| 채팅 위젯 | `gui/chat_widget.py`: 말풍선 형태 명령 입력/응답 표시 |
| 시스템 트레이 | `gui/tray_icon.py`: 트레이 아이콘 + 우클릭 메뉴 |
| 백그라운드 워커 | `gui/workers.py`: QThread 기반 에이전트 실행 |
| Signal/Slot | Brain ↔ GUI 양방향 실시간 통신 |

### Sprint 6 — STT/TTS + 외부 연동

| 작업 | 설명 |
|------|------|
| STT 엔진 | `sensor/stt_engine.py`: Whisper 기반 음성 → 텍스트 |
| TTS 엔진 | `embodiment/tts_engine.py`: 텍스트 → 음성 합성 |
| 외부 DB 연동 | PostgreSQL 또는 Firebase 연결 |
| 전용 앱 / API | 원격에서 에이전트 명령 및 기록 확인 |

---

## 4. 기술 의존성 맵 (구현 순서)

```mermaid
graph TB
    S1["Sprint 1<br/>기반 구축"]
    S2["Sprint 2<br/>Brain + LangGraph"]
    S3["Sprint 3<br/>OS/Office + MCP"]
    S4["Sprint 4<br/>안정화"]
    S5["Sprint 5<br/>PySide6 UI"]
    S6["Sprint 6<br/>STT/TTS + 외부"]

    S1 --> S2
    S2 --> S3
    S3 --> S4
    S4 --> S5
    S5 --> S6

    subgraph Phase1["Phase 1: Core Agent"]
        S1
        S2
        S3
        S4
    end

    subgraph Phase2["Phase 2: UI & Extensions"]
        S5
        S6
    end

    style Phase1 fill:#1a472a,stroke:#2d6a4f
    style Phase2 fill:#1b3a5c,stroke:#2563eb
```

### 모듈별 구현 순서 (의존성 기반)

```mermaid
graph LR
    config["1. config/<br/>설정·DTO·상수"] --> utils["2. utils/<br/>로깅"]
    config --> sensor["3. sensor/<br/>캡처·OCR"]
    config --> embodiment["4. embodiment/<br/>HID·OS·Office"]
    utils --> sensor
    utils --> embodiment

    sensor --> state["5. state/<br/>Blackboard·DB"]
    embodiment --> strategy["6. strategy/<br/>Tools·MCP"]
    state --> brain["7. brain/<br/>LangGraph"]
    strategy --> brain

    brain --> gui["8. gui/<br/>PySide6 (향후)"]
```

---

## 5. 리스크 및 완화 전략

| # | 리스크 | 영향 | 발생 가능성 | 완화 전략 |
|---|--------|------|-----------|----------|
| 1 | Ollama 서버 연결 불안정 | Brain 완전 동작 불가 | 중 | 로컬 Ollama 폴백 설정, 연결 상태 모니터링 |
| 2 | EasyOCR 한글 인식 정확도 부족 | 잘못된 좌표 클릭 | 중 | confidence threshold 조정, PaddleOCR 전환 준비 |
| 3 | LLM이 잘못된 tool_call 생성 | 의도하지 않은 시스템 조작 | 고 | Scope 제한 + Kill Switch + max_steps 제약 |
| 4 | pywin32 COM 호환성 문제 | Office 자동화 실패 | 중 | openpyxl/python-docx 폴백, Office 버전별 테스트 |
| 5 | LangGraph 상태 관리 복잡도 | 디버깅 어려움 | 중 | 상태 로깅 충실화, LangSmith 연동 검토 |
| 6 | 화면 해상도/DPI 차이 | OCR 좌표 오차 | 중 | DPI-aware 좌표 변환 로직 구현 |

---

## 6. 개발 환경 셋업 절차

```bash
# 1. 리포지토리 클론
git clone <repository-url>
cd Desktop_Pet

# 2. Conda 환경 생성
conda env create -f environment.yml
conda activate desktop-pet

# 3. 환경변수 설정
cp .env.example .env
# .env 파일에서 DPET_VLM_ENDPOINT 등 설정

# 4. 데이터 디렉토리 생성
mkdir -p data/screenshots data/logs data/models

# 5. Ollama 서버 연결 확인
curl http://your-ollama-host:11434/api/tags

# 6. 프로젝트 실행 (Phase 1 완료 후)
python main.py --command "테스트 명령"
```

---

## 7. 코딩 컨벤션

| 항목 | 규칙 |
|------|------|
| 타입 힌트 | 모든 함수에 필수 (Python 3.11+ 문법 사용) |
| Docstring | Google 스타일, 한국어 허용 |
| 변수/함수명 | `snake_case` |
| 클래스명 | `PascalCase` |
| 상수 | `UPPER_SNAKE_CASE` |
| 에러 처리 | 커스텀 Exception + `ErrorCode` 명시 |
| 로깅 | `loguru.logger` 사용, print 금지 |
| Import 순서 | stdlib → 서드파티 → 프로젝트 모듈 |
| 파일 인코딩 | UTF-8 |

---

## 8. 환경 변수 목록 (.env.example)

```env
# ══════════════════════════════════════
# Desktop Pet Agent — 환경 변수 설정
# ══════════════════════════════════════

# ── LLM 설정 ──
DPET_VLM_ENDPOINT=http://your-ollama-host:11434
DPET_VLM_MODEL=gemma3:27b
DPET_LLM_TEMPERATURE=0.1
DPET_LLM_MAX_TOKENS=2048

# ── Agent 제약 ──
DPET_MAX_AGENT_STEPS=15
DPET_STEP_TIMEOUT_SECONDS=30
DPET_TOTAL_TIMEOUT_SECONDS=300

# ── Sensor 설정 ──
DPET_SCREEN_CAPTURE_FPS=1.0
DPET_OCR_LANGUAGES=["ko","en"]
DPET_OCR_CONFIDENCE_THRESHOLD=0.3

# ── 안전 설정 ──
DPET_KILL_SWITCH_CLICK_COUNT=6
DPET_KILL_SWITCH_TIME_WINDOW=1.0
DPET_ALLOWED_APPS=[]
DPET_ALLOWED_DIRECTORIES=[]
DPET_DANGEROUS_TOOLS_ENABLED=false

# ── 경로 ──
DPET_DATA_DIR=data
DPET_SCREENSHOTS_DIR=data/screenshots
DPET_LOGS_DIR=data/logs
DPET_DB_PATH=data/desktop_pet.db
```

---

## 9. Conda 환경 정의 (environment.yml)

```yaml
name: desktop-pet
channels:
  - conda-forge
  - pytorch
  - defaults
dependencies:
  - python=3.11
  - pip
  - pip:
    # ── LLM / Agent Framework ──
    - langchain>=0.3
    - langchain-ollama>=0.3
    - langchain-core>=0.3
    - langgraph>=0.2
    - langchain-mcp-adapters>=0.1
    # ── Sensor ──
    - mss>=9.0
    - easyocr>=1.7
    - pywin32>=306
    # ── Embodiment: HID ──
    - pyautogui>=0.9.54
    - pydirectinput>=1.0.4
    - pynput>=1.7
    - pyperclip>=1.8
    # ── Embodiment: Office ──
    - openpyxl>=3.1
    - python-docx>=1.1
    # ── State / Config ──
    - aiosqlite>=0.20
    - pydantic>=2.0
    - pydantic-settings>=2.0
    # ── Utility ──
    - python-dotenv>=1.0
    - jinja2>=3.1
    - loguru>=0.7
    - pillow>=10.0
    # ── (향후) GUI ──
    # - PySide6>=6.6
    # ── (향후) STT/TTS ──
    # - openai-whisper>=20231117
    # - TTS>=0.22
```
