# 제4장 · 도구

> 도구는 에이전트의 손입니다. 도구 분류와 일반 설계 원칙, MCP 프로토콜과 도구 선택의 어려움, 세 가지 도구 유형(인식, 실행, 협업), 이벤트 기반 비동기 에이전트를 다룹니다.

← [한국어 메인 README로 돌아가기](../docs/ko/README.md) · 📖 [제4장 본문 읽기](../book-ko/chapter4.ko.md)

## 실험 읽는 방법

본문은 짧은 메커니즘 skeleton으로 제어 흐름을 설명하고, 실험 디렉터리에는 완전한 SDK 어댑터·로그·테스트·검수 증거를 둡니다. 모든 파일을 줄 단위로 읽을 필요는 없습니다.

- **Starter:** 목표, 최소 명령, 검수 조건부터 시작하고 다음에서 출발하세요: [execution-tools](execution-tools/);
- **Builder:** 진입점, 핵심 루프, 상태/메시지 스키마, 도구와 verifier를 따라갑니다.
- **Maintainer:** 마지막으로 테스트, 증거 manifest, 실패 처리, rollback 경로와 provider adapter를 읽습니다.

첫 읽기에서는 credential, UI, provider 호환 계층을 건너뛰고 수치를 재현할 때 돌아오세요.

## 연계 프로젝트

| 실험 | 프로젝트 | 유형 | 설명 |
| :--: | --- | :--: | --- |
| 4-1 | [perception-tools](perception-tools/) | ✅ | 웹 검색, 멀티모달 이해, 파일 시스템 작업, 공개 데이터 소스 접근 기능을 아우르는 인식 도구 모음을 구축합니다. 대부분 무료 공개 API(DuckDuckGo, Open-Meteo, Yahoo Finance, OpenStreetMap 등)를 사용하므로 API 키가 필요하지 않습니다. |
| 4-2 | [multimodal-agent](multimodal-agent/) | ✅ | Multimodal processing: compare native multimodal, extract-to-text, and tool-based analysis. |
| 4-3 | [execution-tools](execution-tools/) | ✅ | 파일 작업, 코드 인터프리터, 가상 터미널, 외부 시스템 연동을 포함한 안전장치 내장 실행 도구 모음을 구현합니다. 보조 LLM 승인으로 위험한 작업을 막고, 복잡한 출력을 자동으로 요약하며, 코드 문법을 검증합니다. |
| 4-4 | [collaboration-tools](collaboration-tools/) | ✅ | 브라우저 자동화(browser-use 프레임워크), Human-in-the-Loop, 다채널 알림(이메일, Telegram, Slack, Discord), 타이머 관리를 포함한 종합 협업 기능을 제공합니다. 민감한 작업에 대한 관리자 승인과 예약 작업 실행을 지원합니다. |
| 4-5 | [active-tool-discovery](active-tool-discovery/) | ✅ | ‘120개가 넘는 도구 스키마를 모두 주입’하는 방식과 ‘필요할 때 능동적으로 발견’하는 방식을 비교합니다. 후자는 시스템 프롬프트에 몇 가지 기본 도구와 `discover_tools` 메타 도구만 유지하고, 임베딩 유사도로 도구 라이브러리에서 가장 관련 있는 전문 도구 3~5개를 검색합니다. 토큰을 절약하고, 지나치게 긴 목록 때문에 모델이 일반 도구를 잘못 선택하거나 오용하는 문제를 막습니다. |
| — | [active-tool-selection](active-tool-selection/) | ✅ | 미리 정한 도구 집합을 수동적으로 받아들이는 대신, 에이전트가 작업 요구에 따라 가장 적절한 도구 조합을 능동적으로 선택하는 지능형 도구 선택 메커니즘을 구현합니다. |

> 또한 [`chapter4/docker-compose.yml`](docker-compose.yml)과 [`chapter4/DOCKER_DEPLOYMENT.md`](DOCKER_DEPLOYMENT.md)에는 앞서 소개한 MCP 도구 서버를 컨테이너화하고 배포하는 참고 솔루션이 있습니다.

## 프로젝트 유형

| 아이콘 | 유형 | 의미 |
| :--: | --- | --- |
| ✅ | **독립 실행** | 전체 코드가 이 저장소에 있으며, API 키를 설정하면 실행할 수 있습니다. |
| 📖 | **재현 가이드** | **외부 저장소**를 `git clone`해야 하는 상세 안내 문서입니다. |
| 🚧 | **설계 문서** | 아키텍처와 구현 계획만 있으며, 실행 가능한 코드는 아직 작성 중입니다. |
