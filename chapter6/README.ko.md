# 제6장 · 에이전트 평가

> 에이전트 성능을 서로 비교할 수 있는 신호로 바꿉니다. 평가 환경, 데이터셋 설계, 지표 체계, 통계적 유의성, 관측 가능성, 평가 기반 선택, 프로덕션급 내부 평가·시뮬레이션 환경을 다룹니다.

← [한국어 메인 README로 돌아가기](../docs/ko/README.md) · 📖 [제6장 본문 읽기](../book-ko/chapter6.ko.md)

## 연계 프로젝트

| 실험 | 프로젝트 | 유형 | 설명 |
| :--: | --- | :--: | --- |
| 6-1 | `tau2-bench/` | 📖 | τ²-bench의 이중 제어 멀티턴 평가를 실행하고, τ-bench와 작업 정의·성공 조건·사용자 시뮬레이터 설계를 비교합니다. |
| 6-2 | `tau2-bench/` | 📖 | τ²-bench의 난이도별 작업을 직접 수행하고 궤적을 기록합니다. 이는 실험 6-2에서 표본을 추출하는 여섯 가지 벤치마크 중 하나입니다. |
| 6-2 | `terminal-bench/` | 📖 | 실제 터미널 환경에서 AI 에이전트 성능을 시험하는 벤치마크입니다. 코드 컴파일부터 모델 학습, 서버 설정까지 실제 엔드투엔드 작업을 에이전트가 처리하는 방식을 평가합니다. 약 100개 작업으로 구성된 데이터셋과 실행 프레임워크를 포함하며 여러 에이전트 구현을 지원합니다. |
| 6-2 | `SWE-bench/` | 📖 | 대규모 언어 모델이 실제 GitHub Issue를 해결하는 능력을 평가하는 벤치마크입니다. 코드베이스와 Issue 설명을 받은 모델은 문제를 해결하는 패치를 생성해야 합니다. SWE-bench, SWE-bench Lite, SWE-bench Verified, SWE-bench Multimodal 등 여러 버전이 있습니다. |
| 6-2 | `GAIA/` | 📖 | 도구 확장, 효율적인 프롬프팅, 검색 접근 등을 갖춘 차세대 LLM을 평가합니다. 답이 명확하면서도 여러 수준의 도구 사용과 자율성이 필요한 450개 이상의 까다로운 질문을 담고 있으며, 세 가지 난이도로 나뉩니다. |
| 6-2 | `OSWorld/` | 📖 | 파일 관리, 애플리케이션 조작, 시스템 설정 등 완전한 운영체제 환경에서 복잡한 작업을 수행하는 에이전트의 능력을 평가합니다. |
| 6-2, 6-12 | `android_world/` | 📖 | 앱 탐색, UI 상호작용, 작업 완료 능력 등 Android 모바일 환경에서 에이전트 성능을 평가하는 외부 벤치마크 저장소입니다. |
| 6-3 | [user-memory-evaluation](../chapter3/user-memory-evaluation/) | ✅ | 4단계 다차원 루브릭을 60개 사례 × 3개 시스템의 실제 판정 기록 180/180건에 모두 적용했습니다. 독립 검수 인덱스는 차원별 이유와 근거 또는 경계 사례, 환각 발생 시 즉시 탈락 조건을 검증하며 상태는 `complete`입니다. |
| 6-4 | [user-memory-system-evaluation](user-memory-system-evaluation/) | ✅ | 60개 사례 × 3개 시스템의 실제 궤적 180/180건을 오류 없이 수집했고, 원통화 기준 가격도 빠짐없이 반영했습니다. 검수 결과의 상태는 `complete`입니다. |
| 6-5 | [user-memory-policy-eval](user-memory-policy-eval/) | ✅ | JSON, Markdown, Python 유사 메모리 표현에서 11개의 trajectory-prefix 불량 사례를 실제 OpenRouter 호출과 결정론적 정책 검사로 실행합니다. |
| 6-6 | [tts-quality-eval](tts-quality-eval/) | ✅ | 같은 고난도 텍스트 모음을 여러 TTS 설정(모델·음성·속도)으로 합성한 뒤, 멀티모달 LLM-as-a-Judge가 루브릭에 따라 명료도·자연스러움 등 각 항목을 채점합니다. 결과를 재현 가능한 설정 비교표로 집계합니다. |
| 6-7 | [elo-leaderboard](elo-leaderboard/) | ✅ | [전체 정식 검증](elo-leaderboard/validation/runs/exp6-6-arena-20260731-v1/manifest.json)은 공개 Arena 레코드 1,799,991개(블라인드 투표 1,670,250개, 모델 129개)를 처리했습니다. 온라인 Elo와 Bradley-Terry 순위의 Spearman 상관은 0.787, Top-20 중복은 12/20이며, 승률 행렬·월별 스냅샷 17개·도표 3개·D3 애니메이션을 하나의 해시 manifest로 검증했습니다. |
| 6-8 | [model-action-threshold](model-action-threshold/) | ✅ | 동일한 중립적 Coding Harness에서 GPT-5.6-sol과 Claude Sonnet 5가 탐색에서 첫 편집으로 전환하는 임계점을 비교합니다. 18/18 셀이 API 오류 없이 완료됐고, [manifest](model-action-threshold/results/exp6-7-action-threshold-20260731-v1/manifest.json)가 궤적과 요약을 검증 가능한 해시로 연결합니다. |
| 6-9 | [agent-cost-analysis](agent-cost-analysis/) | ✅ | 전형적인 다중 턴 에이전트 작업(고객 서비스 환불)의 전체 비용을 단계별로 분석합니다. 맞춤형 경량 추적 시스템으로 LLM 호출마다 입력·출력·캐시 토큰, 지연 시간, 비용을 기록하고 집계해 가장 비싼 단계를 찾습니다. 이어 A/B 테스트로 KV Cache 친화적 설계와 컨텍스트 압축의 실제 절감 효과를 정량화합니다. |
| 6-10 | [model-benchmark](model-benchmark/) | 🚧 | 여러 OpenAI 호환 LLM API 제공자를 나란히 벤치마크합니다. 스트리밍 인터페이스로 첫 토큰까지 걸린 시간(TTFT)을 정밀 측정하고, 동시 실행 환경에서 엔드투엔드 지연 시간 백분위수(p50/p95), 처리량, 성공률을 계산합니다. 명령 하나로 다차원 비교표를 만들어 모델 선택이 단순한 순위표 이상의 복합적인 절충임을 보여 줍니다. |
| 6-11 | [user-memory-system-evaluation](user-memory-system-evaluation/) | ✅ | 전체 4×3×2×60 매트릭스에서 오류나 미가격 사용 없이 1,440/1,440개의 실제 궤적을 보존했으며, 검색·작업 지표와 상호작용 분석을 완비하고 독립 검증을 통과했습니다. |
| 6-12 | [android-world](android-world/) | 📖 | 이 저장소에 포함된 AndroidWorld T3A 평가 보고서와 실패 분석 노트입니다. 실험 6-12의 출발점이며 벤치마크 원본은 아닙니다. |
| 6-13 | [openvla-robotwin2-eval](openvla-robotwin2-eval/) | ✅ | 단일 GPU 공식 실험에서 action-chunk 군별 256개 에피소드를 완료했습니다. chunk 1은 0/256, chunk 25는 26/256이며 512개 rollout 해시를 보존합니다. |
| — | [public-health-reporting-eval](public-health-reporting-eval/) | ✅ | 합성 DHIS2 형식 집계 데이터로 공중보건 보고 에이전트의 도구 호출, 계산 정확도, 근거 인용, 근거 없는 주장을 객관적으로 평가합니다. |

> 백틱으로 표기한 외부 벤치마크는 별도로 clone해야 합니다. 하이픈이 들어간 [`android-world/`](android-world/)는 이 저장소의 **T3A 평가 분석 노트**([README](android-world/README.md) 참고)이며, 외부 `android_world/` 벤치마크 원본과는 다른 경로입니다.

## 프로젝트 유형

| 아이콘 | 유형 | 의미 |
| :--: | --- | --- |
| ✅ | **독립 실행** | 전체 코드가 이 저장소에 있으며, API 키를 설정하면 실행할 수 있습니다. |
| 📖 | **재현 가이드** | **외부 저장소**를 `git clone`해야 하는 상세 안내 문서입니다. |
| 🚧 | **진행 중** | 구현은 있지만 실험 범위나 검수 증거가 아직 본문의 요구사항을 모두 충족하지 못했습니다. |
