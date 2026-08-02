---
title: AI 에이전트를 깊이 이해하기
description: 핵심 공식 Agent = LLM + 컨텍스트 + 도구를 중심으로, 10개 장에 걸쳐 AI 에이전트를 원리부터 엔지니어링 실전까지 다루는 오픈소스 기술서. 본문·그림·94개 연계 실습을 모두 공개합니다.
---

<div class="hero" markdown>

# AI 에이전트를 깊이 이해하기

**설계 원리와 엔지니어링 실전** · 완전한 오픈소스 AI 에이전트 기술서

<div class="hero-formula" markdown>

`Agent = LLM + 컨텍스트 + 도구`

</div>

<div class="cta-row" markdown>

📥 [한국어 PDF](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ko.pdf){.cta}
📚 [한국어 EPUB](https://github.com/bojieli/ai-agent-book/releases/download/latest/AI-Agents-in-Depth-ko.epub){.cta}

</div>

</div>

---

## 한눈에 보는 구성

<div class="exp-grid" markdown>

<a class="exp-card" href="../book-ko/introduction.ko/">
<span class="exp-title">📖 들어가며</span>
<span class="exp-desc">왜 이 책을 썼는가 · 좋은 설계 원칙은 어떻게 모델 세대 교체를 넘어서는가</span>
</a>

<a class="exp-card" href="../book-ko/chapter1.ko/">
<span class="exp-title">🚀 제1장 · AI 에이전트 기초</span>
<span class="exp-desc">Agent = LLM + 컨텍스트 + 도구 · 경쟁력의 핵심은 하네스 엔지니어링</span>
</a>

<a class="exp-card" href="../book-ko/chapter2.ko/">
<span class="exp-title">🎯 제2장 · 컨텍스트 엔지니어링</span>
<span class="exp-desc">컨텍스트가 능력의 상한을 결정 · KV Cache, 프롬프트 엔지니어링, Agent Skills, 컨텍스트 압축</span>
</a>

<a class="exp-card" href="../book-ko/chapter3.ko/">
<span class="exp-title">📚 제3장 · 사용자 메모리와 지식 베이스</span>
<span class="exp-desc">세션을 넘어 사용자를 기억하고 외부 지식을 연결 · 사용자 메모리, RAG, 구조화 색인, 지식 그래프</span>
</a>

<a class="exp-card" href="../book-ko/chapter4.ko/">
<span class="exp-title">🛠️ 제4장 · 도구</span>
<span class="exp-desc">도구는 에이전트의 두 손 · MCP 프로토콜, 인식·실행·협업 세 종류의 도구, 비동기 에이전트</span>
</a>

<a class="exp-card" href="../book-ko/chapter5.ko/">
<span class="exp-title">💻 제5장 · 코딩 에이전트와 코드 생성</span>
<span class="exp-desc">코드는 '새 도구를 만들 수 있는 도구' · 프로덕션급 코딩 에이전트의 전체 그림</span>
</a>

<a class="exp-card" href="../book-ko/chapter6.ko/">
<span class="exp-title">🎯 제6장 · 에이전트 평가</span>
<span class="exp-desc">성능을 비교 가능한 신호로 · 평가 환경, 지표, 통계적 유의성</span>
</a>

<a class="exp-card" href="../book-ko/chapter7.ko/">
<span class="exp-title">🧠 제7장 · 모델 사후 학습</span>
<span class="exp-desc">SFT와 강화 학습 · 하네스에 쌓인 피드백 신호를 모델 파라미터에 기록</span>
</a>

<a class="exp-card" href="../book-ko/chapter8.ko/">
<span class="exp-title">🌱 제8장 · 에이전트의 지속적 진화</span>
<span class="exp-desc">신뢰할 수 있는 학습 신호에서 지식·지침·프로그램·파라미터 갱신까지</span>
</a>

<a class="exp-card" href="../book-ko/chapter9.ko/">
<span class="exp-title">🎙️ 제9장 · 멀티모달과 실시간 상호작용</span>
<span class="exp-desc">음성 에이전트, Computer Use, 로봇 조작</span>
</a>

<a class="exp-card" href="../book-ko/chapter10.ko/">
<span class="exp-title">🤝 제10장 · 멀티 에이전트 협업</span>
<span class="exp-desc">협업 아키텍처, 실패 유형, 에이전트 사회</span>
</a>

<a class="exp-card" href="../book-ko/afterword.ko/">
<span class="exp-title">📝 후기</span>
<span class="exp-desc">모델이 하네스를 삼키게 될까? 완전한 답과 전망</span>
</a>

</div>

---

## 온라인 읽기 · 다국어

상단 내비게이션 바의 언어 탭으로 전환할 수 있습니다.

| 中文 | 繁體中文（台灣） | English | العربية | Русский | தமிழ் | Tiếng Việt | 日本語 | Türkçe | 한국어 |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| ✅ 원서 | 커뮤니티 번역 | 커뮤니티 번역 | 커뮤니티 번역 | 커뮤니티 번역 | 커뮤니티 번역 | 커뮤니티 번역 | 커뮤니티 번역 | 커뮤니티 번역 | 커뮤니티 번역 |

---

## 소개

- **저장소**: [bojieli/ai-agent-book](https://github.com/bojieli/ai-agent-book)
- **라이선스**: Apache License 2.0
- **이 사이트**: 저장소에 푸시될 때마다 GitHub Actions가 자동으로 다시 빌드합니다

> 💡 이 책의 내용은 계속 갱신되며, 이 사이트는 저장소에 푸시될 때마다 자동으로 다시 빌드됩니다. 전체 PDF가 필요하면 위의 다운로드 버튼을 사용하거나 [Releases](https://github.com/bojieli/ai-agent-book/releases)를 방문하세요.
