Desktop Pet Agent는 사용자의 데스크톱 환경에 투명한 캐릭터 형태로 상주하며, 시각(Vision)과 청각(Audio)을 통해 상황을 인지하고 물리적·소프트웨어적 제어를 통해 복잡한 업무를 대행하는 **멀티모달 AI 자율 행동 에이전트(Multimodal AI Autonomous Embodied Agent)**입니다.

본 프로젝트는 단순한 챗봇이나 정적 스크립트 실행기를 넘어, 다음과 같은 고도화된 아키텍처와 기술적 차별성을 갖춘 진정한 의미의 '데스크톱 보조 시스템'을 목표로 합니다.

1. **범용성 우선 (Generalization First)**
   - 특정 애플리케이션의 API나 자동화 스크립트에 종속되지 않습니다.
   - **'사람처럼 화면을 보고 조작한다'**는 CUA(Computer-Use Agent) 접근 방식을 채택하여, 어떤 프로그램이든 시각적으로 인지하고 마우스/키보드로 제어할 수 있습니다.

2. **순환형 인지 아키텍처 (Cyclical Perception Architecture)**
   - 단순한 프롬프트-응답(Prompt-Response) 방식이 아닌, **LangGraph** 기반의 상태 공유 순환 루프를 통해 자율성을 확보합니다.
   - **Observe → Think → Act → Verify**의 4단계 사이클을 반복하며 스스로 판단하고 행동을 수정합니다.

3. **무한 확장성 (Infinite Extensibility)**
   - **MCP(Model Context Protocol)**를 표준으로 채택하여 외부 도구 및 서비스와의 연결을 지원합니다.
   - 로컬 도구뿐만 아니라 외부 서버의 전문 도구(예: 데이터베이스 관리, API 호출 등)를 동적으로 로드하여 에이전트의 능력을 무한히 확장할 수 있습니다.

4. **안전 최우선 설계 (Safety-First Design)**
   - 하드웨어 킬 스위치(Kill Switch)를 통해 언제든지 시스템을 즉시 중지할 수 있습니다.
   - 모든 행동은 기록되고 감사(Audit)될 수 있으며, 잠재적 위험을 최소화하는 방향으로 설계되었습니다.

5. **점진적 구축 (Incremental Development)**
   - **Phase 1 (Core Agent)**: 에이전트의 인지-추론-행동 파이프라인 구축에 집중합니다.
   - **Phase 2 (UI & Embodiment)**: PySide6를 활용한 투명 펫 UI, 음성 인식(STT), 음성 합성(TTS)을 구현합니다.
   - **Phase 3 (Expansion)**: 외부 데이터베이스 연동 및 전문 애플리케이션 통합을 통해 기능을 고도화합니다.