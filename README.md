# Desktop Pet Agent

Desktop Pet Agent는 사용자의 데스크톱 환경에 상주하며, 시각 및 청각 등 멀티모달 정보를 기반으로 상황을 인지하고 물리적/소프트웨어적 제어를 통해 복잡한 업무를 대행하는 AI 자율 행동 에이전트(Multimodal AI Autonomous Embodied Agent)입니다. 

## 프로젝트 개요
본 프로젝트는 특정 애플리케이션에 종속되지 않는 범용성을 목표로 설계되었습니다. 컴퓨터 화면을 직접 보고 조작하는 CUA(Computer-Use Agent) 방식을 통해 다양한 프로그램과 상호작용합니다. 기초적인 프롬프트 응답 모델을 넘어, **LangGraph** 기반의 '인지-추론-행동-검증(Observe → Think → Act → Verify)' 순환 구조를 채택하여 높은 수준의 자율성을 구현합니다. 또한 **MCP(Model Context Protocol)**를 활용하여 에이전트의 도구 확장성을 무한히 넓힐 수 있습니다.

## 주요 특징
- **범용적 제어**: 운영체제 및 애플리케이션의 제약 없이 화면 인식(Vision)과 마우스/키보드 제어 지원.
- **순환형 루프**: LangGraph 기반 설계로 지속적인 상태 공유 및 자기 수정 행동 수행.
- **도구 확장성**: MCP(Model Context Protocol)를 통한 외부 서버 및 로컬 도구의 동적 연동.
- **안전성 확보**: 하드웨어 킬 스위치(Kill Switch)를 내장하여 비상 시 에이전트 강제 종료 가능.

## 폴더 구조
프로젝트는 기능별로 모듈화되어 관리됩니다.

```text
Desktop_Pet/
│  [1. 인식 - Perception]
├── sensor/         # 시각, 청각 등 센서 기반 입력 데이터 수집 모듈 (스크린 캡처, OCR 등)
│  [2. 사고 - Reasoning]
├── brain/          # LangGraph 에이전트 순환 루프, LLM 추론 노드, 프롬프트 정의
│  [3. 행동 - Action]
├── strategy/       # 에이전트 행동 전략: 통제 가능한 도구(Tool) 레지스트리 관리 및 MCP 연동
├── embodiment/     # 에이전트 물리/OS 제어: HID(키보드/마우스), OS 조작, Word 자동화, 킬 스위치
│  [4. 기억 - Memory]
├── state/          # 시스템/앱의 현재 상태(Blackboard) 및 장기 기억(DB) 저장
│  [5. 기반 - Foundation]
├── config/         # 시스템 전역 설정(Pydantic), DTO, 상수 (constants, settings, types_dto)
├── utils/          # 로거(logger.py) 등 프로젝트 전역에서 사용되는 공통 유틸리티
├── data/           # 실행 중 발생되는 로그, 스크린샷, 생성된 작업물(results) 저장 공간
├── tests/          # 단위 테스트 및 통합 테스트 코드
├── gui/            # 에이전트 캐릭터 UI 화면 (PySide6 등 사용), 자산(assets) 데이터 (Phase 2)
├── docs/           # 프로젝트 관련 기획서, 다이어그램, 개발 일지(Development_Walkthrough)
│
├── main.py         # 애플리케이션 진입점 (Entry Point), CLI 기반 실행 인터페이스
└── README.md       # 프로젝트 개요 및 실행, 관리 방법 안내
```

## 실행 방법

### 사전 요구사항
- Python 3.11 이상 권장
- **Conda 환경 사용 (필수)**: `desktoppet` 가상 환경 활성화
- **VLM 로컬 모델 (필수)**: Ollama를 통해 `qwen3-vl:8b` 모델 설치 (`ollama pull qwen3-vl:8b`)

### 에이전트 실행

먼저 conda 환경을 활성화한 후, 디렉토리에서 `main.py`를 실행하여 에이전트를 가동합니다.

```bash
conda activate desktoppet
```

1. **대화형 모드 실행**
사용자와 지속적으로 상호작용하며 명령을 입력받습니다.
```bash
python main.py
```

2. **단일 명령 모드 실행**
특정 업무를 에이전트에게 1회 지시하고 결과를 확인합니다.
```bash
python main.py --command "Word 문서를 작성해줘"
```

3. **기타 옵션 (디버깅용)**
에이전트 제어 중지 기능(Kill Switch)을 끄고 실행할 수 있습니다 (권장하지 않음).
```bash
python main.py --no-kill-switch
```

### 🛑 긴급 정지 (Kill Switch)
데스크톱 제어 중 시스템 오작동이나 무한 루프 등 비상 상황 발생 시, **마우스 우클릭을 10회 빠르게 연타 (1.5초 이내)**하면 시스템 방어 메커니즘이 작동하며 즉시 에이전트가 강제 종료됩니다.