# 제1장 · 에이전트 기초

> ‘모델이 곧 에이전트’라는 새로운 패러다임에서 출발해 **에이전트 = LLM + 컨텍스트 + 도구**라는 핵심 공식을 세우고, 모델 밖의 모든 엔지니어링 역량이 진정한 경쟁력이라는 하네스 엔지니어링을 소개합니다.

← [한국어 메인 README로 돌아가기](../docs/ko/README.md) · 📖 [제1장 본문 읽기](../book-ko/chapter1.ko.md)

## 실험 읽는 방법

본문은 짧은 메커니즘 skeleton으로 제어 흐름을 설명하고, 실험 디렉터리에는 완전한 SDK 어댑터·로그·테스트·검수 증거를 둡니다. 모든 파일을 줄 단위로 읽을 필요는 없습니다.

- **Starter:** 목표, 최소 명령, 검수 조건부터 시작하고 다음에서 출발하세요: [context](context/);
- **Builder:** 진입점, 핵심 루프, 상태/메시지 스키마, 도구와 verifier를 따라갑니다.
- **Maintainer:** 마지막으로 테스트, 증거 manifest, 실패 처리, rollback 경로와 provider adapter를 읽습니다.

첫 읽기에서는 credential, UI, provider 호환 계층을 건너뛰고 수치를 재현할 때 돌아오세요.

## 연계 프로젝트

| 실험 | 프로젝트 | 유형 | 설명 |
| :--: | --- | :--: | --- |
| 1-1 | [context](context/) | ✅ | 체계적인 구성 요소 제거 실험을 통해 에이전트 컨텍스트를 이루는 각 요소의 중요성을 보여 줍니다. 여러 LLM 제공자(SiliconFlow Qwen, ByteDance Doubao, Moonshot Kimi)를 지원하며, 컨텍스트 모드를 바꾸어 에이전트 행동이 어떻게 달라지는지 관찰할 수 있습니다. |
| 1-2 | [web-search-agent](web-search-agent/) | ✅ | 여러 차례 검색하고 정보를 종합하는 기본적인 심층 검색 에이전트를 구현합니다. |
| 1-3 | [search-codegen](search-codegen/) | 🚧 | GPT-5 공식 Responses API의 호스팅 검색과 코드 인터프리터 경로를 완전히 구현했지만, 공식 실측 두 번 모두 할당량 부족으로 429 응답을 받았습니다. OpenRouter는 인터페이스 진단에만 사용했으며 본문 검수를 대신하지 않습니다. |
| 1-4 | [image-gen-workflow](image-gen-workflow/) | ✅ | 구체적/광범위한 두 유형의 요구 × 워크플로(kimi-k3 재작성 + Tongyi Wanxiang)와 네이티브(Gemini / GPT-Image 2) 두 경로의 실제 비교: 구체적 요구에서는 네이티브 경로가 더 충실(재작성 노드가 포스터 문구를 부정 프롬프트에 넣어버림); 광범위한 요구에서는 재작성의 장면 구체화가 상상력을 더하지만 GPT-Image 2가 스스로 관점을 보완할 수 있음—어댑터 층이 모델에 내재화된다는 실증 |
| 7-1, 7-2 | [learning-from-experience](learning-from-experience/) | ✅ | Q-learning 10,000회와 평가 100회, 공식 Kimi K3의 첫 에피소드까지 두 방식을 실측해 검수를 마쳤습니다. [증거](learning-from-experience/validation/20260730_011704/evidence.json)에는 Kimi가 17단계 만에 성공하고 fallback을 사용하지 않은 사실과 과거 점 추정치와의 차이가 기록돼 있습니다. |

## 프로젝트 유형

| 아이콘 | 유형 | 의미 |
| :--: | --- | --- |
| ✅ | **독립 실행** | 전체 코드가 이 저장소에 있으며, API 키를 설정하면 실행할 수 있습니다. |
| 📖 | **재현 가이드** | **외부 저장소**를 `git clone`해야 하는 상세 안내 문서입니다. |
| 🚧 | **설계 문서** | 아키텍처와 구현 계획만 있으며, 실행 가능한 코드는 아직 작성 중입니다. |
