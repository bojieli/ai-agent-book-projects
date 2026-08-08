# 제7장 · 모델 사후 학습

> 사전 학습, SFT, RL이라는 세 단계를 종합적으로 살펴봅니다. SFT와 RL을 선택하는 기준, RLHF, 알고리즘 비교, 데이터와 환경을 다루고, 모델에 도구 호출을 가르치고 샘플 효율성을 높이기 위한 최신 연구를 탐구합니다.

← [한국어 메인 README로 돌아가기](../docs/ko/README.md) · 📖 [제7장 본문 읽기](../book-ko/chapter7.ko.md)

## 연계 프로젝트

| 실험 | 프로젝트 | 유형 | 설명 |
| :--: | --- | :--: | --- |
| 7-1, 7-2 | [learning-from-experience](../chapter1/learning-from-experience/) | ✅ | 동일한 결정론적 보물찾기 환경에서 Q-learning 10,000회, 탐욕 정책 평가 100회, 공식 Moonshot `kimi-k3`의 첫 에피소드 실측을 완료했습니다. [두 실험군의 증거](../chapter1/learning-from-experience/validation/20260730_011704/evidence.json)에 원본 API 응답 기록 17/17건을 보존했으며 fallback은 없었습니다. |
| 7-3 | [MiniMind-pretrain](MiniMind-pretrain/) | ✅ | [정식 학습 보고서](MiniMind-pretrain/validation/runs/exp7-3-training-report-20260731-v1/report.md)는 원본 및 QK-Norm+Muon 모델의 사전 학습·SFT·DPO 단계에서 나온 역사적 출력 49개, 익명 ARK 심사 8회, 고정된 소스·데이터·환경 재현 계약을 보존합니다. 역사적 체크포인트는 배포하지 않으며 승인 요건이 아닙니다. |
| 7-4 | [MiniMind-pretrain](MiniMind-pretrain/) | ✅ | [정식 학습 보고서](MiniMind-pretrain/validation/runs/exp7-4-training-report-20260731-v1/report.md)는 8개 VLM 구성 × 8개 이미지의 역사적 출력 64개, 실제 이미지 기반 익명 ARK 심사 8회, 고정된 소스·데이터·CLIP·평가 이미지 해시를 보존합니다. 원본 SFT가 1.9062로 가장 높았고 동일 SFT 기반 QK-Norm+Muon 비교는 개선되지 않았다는 부정적 결과도 명시합니다. 역사적 체크포인트는 배포하지 않으며 승인 요건이 아닙니다. |
| 7-5 | [continued-pretraining](continued-pretraining/) | ✅ | [정식 학습 보고서](continued-pretraining/validation/runs/exp7-5-training-report-20260731-v1/report.md)는 RTX 4090 3단계 원시 출력, 15개 생성, 5회 익명 ARK 심사, 소스 해시와 현재 재현 revision을 결합합니다. 최종 한국어는 +1.7777, 영어는 -0.8333이었고 김치 사실 오류도 명시했습니다. 체크포인트는 배포하지 않으며 승인 요건이 아닙니다. |
| 7-6 | [sesame](sesame/) · [orpheus](orpheus/) | 🚧 | 준언어 태그 모델링과 문장 간 음색 일관성을 다루는 두 가지 실제 음성 SFT 트랙입니다. 학습 후 어댑터, 음성 결과물, 수동·자동 비교 증거가 있어야 완료로 봅니다. |
| 7-7 | [MultilingualReasoning](MultilingualReasoning/) | 🚧 | 다국어 사고 SFT 구현입니다. 학습 체크포인트와 언어 간 벤치마크의 학습 전후 비교가 있어야 완료로 봅니다. |
| 7-8 | [prompt-distillation](../chapter8/prompt-distillation/) | ✅ | 교사 모델의 프롬프트·응답 생성, 학생 모델 학습, 품질·비용 비교를 다루는 장 간 연계 구현입니다. 예시 생성이나 프롬프트 메커니즘만으로는 완료로 보지 않습니다. |
| 7-9 | [cot-distillation](cot-distillation/) | 🚧 | 실제 교사 CoT 궤적을 생성하고 규칙으로 필터링했습니다. 학생 모델을 학습하고 수학·코딩 성능 향상과 성찰·되돌아가기·검증 행동을 확인해야 합니다. |
| 7-10 | [AdaptThink 연계 설명](AdaptThink/) · `AdaptThink-original/` | 📖 | 외부 `bojieli/AdaptThink` 학습 코드로, 문제 난이도에 따라 Thinking 또는 NoThinking을 선택하도록 모델을 학습합니다. |
| 7-11 | `SFTvsRL/` | 📖 | `bojieli/SFTvsRL`의 GeneralPoints-L/VL로, 동일한 예산에서 SFT와 PPO의 ID/OOD 기억·일반화 성능을 비교합니다. |
| 7-12 | [SpatialReasoning 연계 설명](SpatialReasoning/) · `SFTvsRL/` | 📖 | 동일한 `bojieli/SFTvsRL` 체크아웃에서 V-IRL-L/VL 학습과 도시 간·규칙 OOD 평가를 수행하며, 별도의 SpatialReasoning 코드 저장소가 아닙니다. |
| 7-13 | [SimpleVLA-RL 연계 설명](SimpleVLA-RL/) · `SimpleVLA-RL/SimpleVLA-RL/` | 📖 | `PRIME-RL/SimpleVLA-RL` 주 저장소와 내부 `verl/`은 고정되어 있습니다. OpenVLA-OFT, LIBERO/RoboTwin, 체크포인트, Flash Attention, CUDA/드라이버, 시뮬레이터 자산을 아우르는 완전한 의존성 잠금 상태는 아직 검증되지 않았습니다. |
| 7-14 | [retool 연계 설명](retool/) · `verl/` · `SandboxFusion/` | 📖 | ReTool 레시피는 `bojieli/verl`에서 가져오며 실시간 코드 실행은 `bojieli/SandboxFusion`에 의존합니다. `retool`이라는 별도의 소스 저장소는 없습니다. |
| 7-15 | [AWorld-train 연계 설명](AWorld-train/) · `AWorld/` | 📖 | `bojieli/AWorld`의 GAIA MCP 샌드박스와 학습 진입점을 사용하며, 학습 백엔드는 `bojieli/verl`입니다. |
| 7-16 | [RLVP 연계 설명](RLVP/) · `RLVP/rlvp/` | 📖 | 전체 학습·평가 코드는 `1ad30bc…`에 고정된 `19PINE-AI/rlvp`에서 가져옵니다. 현재 체크아웃이 없어 학습은 실행하지 않았습니다. |
| 7-17 | [premature-completion-dpo](premature-completion-dpo/) | ✅ | GPU에서 조기 완료 bad case를 DPO로 수정합니다. |
| 7-18 | [curly-quote-sft](curly-quote-sft/) | ✅ | 감사된 범위 민감 중국어 곡선 따옴표 SFT: 10개 문서 유형·9개 프로그래밍 언어에서 train/holdout/boundary 1024/256/256개; Qwen3-8B exact 96.9%/97.7%, 보호 영역 보존 100%. |
| 7-19 | [exact-copy-sft](exact-copy-sft/) | ✅ | 감사된 특수 문자열 byte-exact 복사 SFT: 1024/256/256개; Qwen3-8B holdout 78.9%, boundary 80.1%, Qwen3/Qwen2.5/Mistral tokenizer 감사 포함. |
| — | `verl/` | 📖 | verl은 대규모 언어 모델의 RLHF 학습을 위해 설계된 효율적인 강화 학습 프레임워크로, PPO, GRPO, DAPO 등 여러 알고리즘을 지원합니다. |
| — | [Intuitor](Intuitor/) | ✅ | 모델의 직관적 사고 능력을 학습해 상세한 사고 사슬 없이도 빠르고 합리적인 판단을 내릴 수 있게 합니다. |
| — | `tinker-cookbook/` | 📖 | 모델 학습을 위한 여러 실전 팁과 모범 사례를 모았습니다. |

## 프로젝트 유형

| 아이콘 | 유형 | 의미 |
| :--: | --- | --- |
| ✅ | **독립 실행** | 전체 코드가 이 저장소에 있으며, API 키를 설정하면 실행할 수 있습니다. |
| 📖 | **재현 가이드** | **외부 저장소**를 `git clone`해야 하는 상세 안내 문서입니다. |
| 🚧 | **진행 중** | 구현은 있지만 학습 또는 본문 기준의 검증 증거가 아직 완전하지 않습니다. |
