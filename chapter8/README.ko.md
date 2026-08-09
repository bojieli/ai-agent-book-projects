# 제8장 · 에이전트의 지속적 진화

> 가중치를 바꾸지 않고도 성장하는 방법을 다룹니다. 세 가지 학습 패러다임, 경험으로부터의 학습, ‘도구 사용자’에서 ‘도구 제작자’로 나아가는 과정을 통해 에이전트가 ‘똑똑함’을 넘어 ‘능숙함’을 갖추게 합니다.

← [한국어 메인 README로 돌아가기](../docs/ko/README.md) · 📖 [제8장 본문 읽기](../book-ko/chapter8.ko.md)

## 연계 프로젝트

| 실험 | 프로젝트 | 유형 | 설명 |
| :--: | --- | :--: | --- |
| 8-1 | [trajectory-verifier](trajectory-verifier/) | ✅ | 실제 고객 서비스 호출 28건, Judge 호출 8건, 전문가 표본 8건을 검수했습니다. [증거](trajectory-verifier/validation/real_20260729T165247Z/evidence.json)에는 핵심 위반의 안정성 주장이 재현되지 않은 사실도 함께 기록돼 있습니다. |
| 8-2 | [gaia-experience](gaia-experience/) | ✅ | 실제 GAIA 궤적 세 그룹과 지식 문서 대조를 검수했습니다. [증거](gaia-experience/validation/real_20260729T164012Z/evidence.json)에는 지식 문서 그룹이 25%, 두 대조군이 각각 50%였던 부정적 결과가 기록돼 있습니다. |
| 8-3 | [prompt-auto-optimization](prompt-auto-optimization/) | ✅ | 실제 작업 에이전트, LLM Judge, 코딩 에이전트로 초기·자동·수동 세 그룹의 전체 보존 세트와 경계 세트를 실행했으며, 원본 응답과 배포 기준을 보존했습니다. |
| 8-4 | 본문 대조 실험 | 🚧 | 실험 8-4: 사용자 피드백에서 요구사항 명확화 Skill을 진화시킵니다 |
| 8-5 | [browser-use-rpa](browser-use-rpa/) | ✅ | 실험 8-5: 브라우저 궤적을 상태 서술어가 포함된 워크플로로 컴파일합니다 |
| 8-6 | [self-modifying-agent](self-modifying-agent/) | ✅ | 실험 8-6: 반복 장애에서 패치를 만들고 동일한 배포 게이트를 거칩니다 |
| 8-7 | [harness-safety-gate](harness-safety-gate/) | ✅ | 실험 8-7: 고위험 작업 확인 게이트 |
| 8-8 | [hermes-self-evolution](hermes-self-evolution/) | 📖 | 실험 8-8: Hermes에게 책 전체와 자기 소스를 줍니다 |
| 8-9 | [self-evolution-eval](self-evolution-eval/) | ✅ | 실험 8-9: 학습·전이·규칙 교체·보존을 평가합니다 |

위 실험은 모두 API 키 없이 실행할 수 있는 오프라인 진입점과 단위 테스트를 사전 점검용으로 유지합니다. 표의 ✅는 각 디렉터리에 보존된 실제 모델·궤적·브라우저의 정식 증거를 근거로 하며, 오프라인 동작 시연으로 대신하지 않습니다. 과거의 수치나 정성적 주장이 재현되지 않았을 때도 부정적 결과를 증거에 그대로 기록합니다.

## 보충 사례

| 실험 | 프로젝트 | 연관성 |
| :--: | --- | --- |
| 7-8 | [prompt-distillation](prompt-distillation/) | 프롬프트 증류와 파라미터 기반 학습을 다루는 장 간 프로젝트입니다. 학습 방법 자체는 제7장에 속합니다. |
| — | [self-evolving-tools](self-evolving-tools/) | Alita 방식의 도구 발견·캡슐화·재사용을 보여 주는, ‘경험을 프로그램에 기록하기’의 보충 사례입니다. |
| — | [ai-style-skill](ai-style-skill/) | 글쓰기 Skill의 보충 사례입니다. 주요 예시는 제2장에 등장합니다. |

## 프로젝트 유형

| 아이콘 | 유형 | 의미 |
| :--: | --- | --- |
| ✅ | **독립 실행** | 전체 코드가 이 저장소에 있으며, API 키를 설정하면 실행할 수 있습니다. |
| 📖 | **재현 가이드** | **외부 저장소**를 `git clone`해야 하는 상세 안내 문서입니다. |
| 🚧 | **진행 중** | 구현은 있지만 실제 데이터·환경 또는 장기 검수 증거가 아직 완전하지 않습니다. |
