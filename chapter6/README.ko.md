# 제6장 · 상호작용: 관찰 공간과 행동 공간의 확장

> 인식과 행동의 범위를 텍스트에서 음성, GUI, 물리 세계로 넓힙니다. 세 가지 음성 패러다임(캐스케이드, 종단 간 옴니모달, 전이중/상호작용형), 스트리밍 음성 인식·합성, Computer Use, 로봇 조작을 다룹니다.

← [한국어 메인 README로 돌아가기](../docs/ko/README.md) · 📖 [제6장 본문 읽기](../book-ko/chapter6.ko.md)

## 실험 읽는 방법

본문은 짧은 메커니즘 skeleton으로 제어 흐름을 설명하고, 실험 디렉터리에는 완전한 SDK 어댑터·로그·테스트·검수 증거를 둡니다. 모든 파일을 줄 단위로 읽을 필요는 없습니다.

- **Starter:** 목표, 최소 명령, 검수 조건부터 시작하고 다음에서 출발하세요: [live-audio](live-audio/);
- **Builder:** 진입점, 핵심 루프, 상태/메시지 스키마, 도구와 verifier를 따라갑니다.
- **Maintainer:** 마지막으로 테스트, 증거 manifest, 실패 처리, rollback 경로와 provider adapter를 읽습니다.

첫 읽기에서는 credential, UI, provider 호환 계층을 건너뛰고 수치를 재현할 때 돌아오세요.

## 연계 프로젝트

| 실험 | 프로젝트 | 유형 | 설명 |
| :--: | --- | :--: | --- |
| 6-1 | [agent-with-event-trigger](agent-with-event-trigger/) | ✅ | FastAPI로 만든 현대적인 이벤트 기반 에이전트입니다. 기본 설정으로 앞선 세 MCP 서버의 모든 도구를 통합합니다. 네이티브 비동기 아키텍처로 MCP 도구를 깔끔하게 불러오며, HTTP API를 통해 웹·인스턴트 메시징·GitHub·타이머 등 여러 출처의 이벤트를 받습니다. 자동 API 문서(Swagger UI)와 백그라운드 모니터링 기능도 제공합니다. |
| 6-2 | [async-agent](async-agent/) | ✅ | 단일 스레드 asyncio 모델을 바탕으로 이벤트 기반 비동기 에이전트 프레임워크(Flux)의 핵심을 구현합니다. 받은 편지함 이벤트 큐가 긴급도(interrupt/immediate/queue)에 따라 작업을 배분하고, 비동기 도구의 병렬 실행, 실행 중인 턴 중단, 모의 장기 실행 작업의 취소·상태 조회를 지원합니다. 의사결정에는 실제 LLM의 함수 호출을 사용합니다. |
| 6-3 | [live-audio](live-audio/) | ✅ | VAD + ASR(Whisper/SenseVoice) + LLM(GPT-4o/Gemini/Doubao) + TTS(Fish Audio)를 통합한 실시간 음성 채팅으로, WebSocket을 통해 짧은 지연 시간을 제공합니다. |
| Add-on | [phone-agent](phone-agent/) | ✅ | 로컬 WebRTC 프로젝트는 브라우저 마이크 RTP, 로컬 Whisper, 실제 외부 LLM, TTS 및 하향 RTP를 사용하는 직접/ReAct 실행을 보존하며 두 경로 모두 20/20 게이트를 통과합니다. PSTN/E.164는 이 로컬 범위에 포함되지 않습니다. [manifest](phone-agent/validation/runs/phone-agent-webrtc-audio-20260731-v1/manifest.json)에 역사적 실행 식별자를 보존합니다. |
| 6-4 | [streaming-speech](streaming-speech/) | ✅ | 실제 Qwen2-Audio에서 누적되는 음성 접두부 전체를 매번 다시 인코딩해 음향 이벤트를 감지하고 청크별 지연 시간을 측정합니다. 이를 600ms VAD + 오픈 소스 Whisper 조합과 일반·쉼·소음 세 시나리오에서 비교합니다. |
| 6-5 | [end-to-end-speech](end-to-end-speech/) | ✅ | 고정 revision의 MiniCPM-o 4.5를 RTX PRO 6000 한 장에서 실제 로컬 실행했습니다. end-to-end와 self-cascade 모두 3/4였지만 의미/준언어 오류가 상호 보완적이었고, 실제 24kHz 음성 출력과 검증 증거를 보존했습니다. |
| 6-6 | [controllable-tts](controllable-tts/) | 🚧 | 실제 Fish Audio S1의 4×3×2=24개 참조 음성 라이브러리와 A/B/C 미디어가 구조 검사를 통과했습니다. 다만 [검수 결과](controllable-tts/validation/acceptance.json)에는 정성 청취 평가와 ‘사람 상담원에 가까움’이라는 주장에 대한 평가가 아직 없다고 명시되어 있습니다. |
| 6-7 | `claude-quickstarts/computer-use-demo/` | 📖 | `anthropics/claude-quickstarts`를 `9bcc95e…`에 고정해 사용합니다. 본문이 다루는 것은 전체 quickstarts 모음이 아니라 컨테이너 기반 Ubuntu 데스크톱과 Claude Computer Use 에이전트 루프로 구성된 `computer-use-demo/`입니다. |
| 6-8 | `browser-use/` | 📖 | 외부 `browser-use/browser-use` 저장소를 `ec9277c…`에 고정해 사용합니다. 본문 과제에서는 시각 입력을 사용하는 CLI(`use_vision=True`)로 Google에서 샌프란시스코 날씨를 검색하고 동작 및 스크린샷 궤적을 보관합니다. |
| 6-9 | [xlerobot-teleoperation](xlerobot-teleoperation/) | 📖 | 실제 XLeRobot을 원격 조작해 같은 책상 정리 과제를 수행합니다. 빨간 컵은 쟁반에, 노란 폐지는 쓰레기통에 넣고 마지막에 다시 관찰·검증합니다. |
| 6-10 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | 같은 책상 과제의 이상적 제어 상한을 시뮬레이터에서 측정합니다. 실제 로봇 실행을 뜻하지 않습니다. |
| 6-11 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | Gemini Robotics-ER 1.5가 실제 XLeRobot을 자율 제어해 같은 책상 정리 과제를 수행합니다. |
| 6-12 | [gemini-xlerobot-navigation](gemini-xlerobot-navigation/) | 📖 | 시뮬레이터에서 같은 과제의 오픈 루프, 단계별 확인, 예측형 폐루프를 비교합니다. |
| 6-13 | [rgb-sim2real-grasping](rgb-sim2real-grasping/) | 📖 | 배경·물체 외관·조명·시각 노이즈를 바꾸며 같은 과제를 RGB 환경 간에 평가합니다. |

## 프로젝트 유형

| 아이콘 | 유형 | 의미 |
| :--: | --- | --- |
| ✅ | **독립 실행** | 전체 코드가 이 저장소에 있으며, API 키를 설정하면 실행할 수 있습니다. |
| 📖 | **재현 가이드** | **외부 저장소**를 `git clone`해야 하는 상세 안내 문서입니다. |
| 🚧 | **진행 중** | 구현은 있지만, 본문에서 요구하는 실제 실행, 승인된 참여자, 하드웨어 또는 검수 증거가 아직 완전하지 않습니다. |
