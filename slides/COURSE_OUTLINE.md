# AI Agents in Depth — English Video Course

Approved Option B curriculum: 42 problem-oriented lessons following the English book order. Each lesson is 15–20 minutes, budgeting approximately one minute per Slidev slide plus one to three minutes per live experiment.

## Learning arc

| Movement | Chapters | Viewer progression |
| --- | --- | --- |
| Build an Agent | Introduction–Chapter 5 | Context → memory → tools → executable capabilities |
| Improve it scientifically | Chapters 6–8 | Evaluation → post-training → continual evolution |
| Expand it | Chapters 9–10 | Voice → Computer Use → robotics → multi-Agent collaboration |

## Approved chapter allocation

| Book section | Lessons | Count |
| --- | ---: | ---: |
| Introduction | 1 | 1 |
| Chapter 1 | 2–4 | 3 |
| Chapter 2 | 5–9 | 5 |
| Chapter 3 | 10–13 | 4 |
| Chapter 4 | 14–17 | 4 |
| Chapter 5 | 18–21 | 4 |
| Chapter 6 | 22–25 | 4 |
| Chapter 7 | 26–31 | 6 |
| Chapter 8 | 32–34 | 3 |
| Chapter 9 | 35–38 | 4 |
| Chapter 10 | 39–42 | 4 |
| **Total** | **1–42** | **42** |

Chapter 7 intentionally receives six lessons because post-training and reinforcement learning are the largest conceptual jump for viewers without prior ML-training knowledge. Chapter 9 receives four lessons so Computer Use and robotics have separate mechanisms, experiments, and safety boundaries.

## Lesson-by-lesson outline

### Introduction

| Lesson | Problem-oriented title | Main learning outcome | Live anchor(s) | Slides | Demo | Target |
| ---: | --- | --- | --- | ---: | ---: | ---: |
| [01](lesson-01.md) | How Do We Replace Agent Intuition with Evidence? | A practice-first map of AI Agents in Depth | Course tour | 15 | 1 min | 16 min |

### Chapter 1

| Lesson | Problem-oriented title | Main learning outcome | Live anchor(s) | Slides | Demo | Target |
| ---: | --- | --- | --- | ---: | ---: | ---: |
| [02](lesson-02.md) | What Makes an AI System an Agent? | Reasoning engine + working context + action interfaces | 1-2 | 15 | 2 min | 17 min |
| [03](lesson-03.md) | Why Does an Agent Need Its Entire Trajectory? | ReAct, context components, and systematic ablation | 1-1A, 1-1B | 15 | 4 min | 19 min |
| [04](lesson-04.md) | Why Doesn't a Stronger Model Make a Reliable Agent? | Harness engineering, orchestration, and guardrails | 1-3 | 15 | 2 min | 17 min |

### Chapter 2

| Lesson | Problem-oriented title | Main learning outcome | Live anchor(s) | Slides | Demo | Target |
| ---: | --- | --- | --- | ---: | ---: | ---: |
| [05](lesson-05.md) | What Does the Model Actually See? | Messages, tool calls, and the Agent core loop | 2-1 | 15 | 3 min | 18 min |
| [06](lesson-06.md) | Why Can One Timestamp Make an Agent Slow? | Chat templates, attention, KV Cache, and stable prefixes | 2-3, 2-2 | 15 | 4 min | 19 min |
| [07](lesson-07.md) | Why Do Better Prompts Need Structure, Not More Rules? | Process-oriented instructions, tool definitions, and injection boundaries | 2-4, 2-5 | 13 | 5 min | 18 min |
| [08](lesson-08.md) | How Can an Agent Know What It Needs to Learn? | Skills, progressive disclosure, and on-demand capability | 2-6 | 15 | 3 min | 18 min |
| [09](lesson-09.md) | How Can an Agent Stay Oriented in a Long Task? | Status bars, physical time, context rot, and compression | 2-8, 2-9 | 15 | 4 min | 19 min |

### Chapter 3

| Lesson | Problem-oriented title | Main learning outcome | Live anchor(s) | Slides | Demo | Target |
| ---: | --- | --- | --- | ---: | ---: | ---: |
| [10](lesson-10.md) | What Should an Agent Remember About a User? | Memory levels, representations, evaluation, and privacy | 3-1/3-2, 3-3 | 14 | 5 min | 19 min |
| [11](lesson-11.md) | Why Does Semantic Search Miss Exact Answers? | Chunking, dense retrieval, sparse retrieval, and evaluation | 3-4, 3-5 | 15 | 4 min | 19 min |
| [12](lesson-12.md) | Why Is One Retrieval Index Never Enough? | Hybrid search, reranking, multimodality, and structured knowledge | 3-6, 3-8 | 13 | 5 min | 18 min |
| [13](lesson-13.md) | When Should the Agent Decide What to Retrieve? | Agentic RAG, contextual retrieval, and two-tier memory | 3-9, 3-11, 3-12 | 13 | 6 min | 19 min |

### Chapter 4

| Lesson | Problem-oriented title | Main learning outcome | Live anchor(s) | Slides | Demo | Target |
| ---: | --- | --- | --- | ---: | ---: | ---: |
| [14](lesson-14.md) | What Makes a Tool Easy for a Model to Use? | Capability boundaries, granularity, descriptions, and MCP | 4-1 | 15 | 3 min | 18 min |
| [15](lesson-15.md) | How Do You Let an Agent Act Without Letting It Cause Damage? | Execution tools, independent checks, and fail-closed design | 4-3A, 4-3B | 15 | 3 min | 18 min |
| [16](lesson-16.md) | When Should an Agent Ask for Help or Delegate? | Sub-agents, Human-in-the-Loop, and communication tools | 4-4A, 4-4B | 15 | 3 min | 18 min |
| [17](lesson-17.md) | How Can a Synchronous Model Live in an Asynchronous World? | Events, interruption, parallelism, and proactive tool discovery | 4-5, 4-6, 4-7 | 13 | 6 min | 19 min |

### Chapter 5

| Lesson | Problem-oriented title | Main learning outcome | Live anchor(s) | Slides | Demo | Target |
| ---: | --- | --- | --- | ---: | ---: | ---: |
| [18](lesson-18.md) | Why Is Code Generation Not Enough to Build a Coding Agent? | Files, execution, harness recovery, and bounded verification | Coding workflow, Harness tests | 15 | 3 min | 18 min |
| [19](lesson-19.md) | When Should an Agent Think in Code Instead of Words? | Math, logic, and deterministic business constraints | 5-1, 5-2, 5-3 | 13 | 6 min | 19 min |
| [20](lesson-20.md) | How Can an Agent Create Media It Can Actually Verify? | Slidev, rendering, multimodal review, and video editing | 5-4, 5-6 | 13 | 5 min | 18 min |
| [21](lesson-21.md) | How Can Code Let an Agent Create New Capabilities? | Adapters, generative UI, hot repair, and Agent bootstrapping | 5-7, 5-9, 5-12 | 13 | 6 min | 19 min |

### Chapter 6

| Lesson | Problem-oriented title | Main learning outcome | Live anchor(s) | Slides | Demo | Target |
| ---: | --- | --- | --- | ---: | ---: | ---: |
| [22](lesson-22.md) | How Do You Test an Agent Instead of Its Final Answer? | Environments, state, datasets, and executable verification | Evaluation control | 16 | 2 min | 18 min |
| [23](lesson-23.md) | How Do You Judge Quality Without Hiding Failure? | Rubrics, vetoes, LLM judges, pairwise comparison, and Elo | 6-3, 6-6 | 15 | 4 min | 19 min |
| [24](lesson-24.md) | Which Agent Should You Ship? | Model behavior, latency, cost, and evaluation-driven selection | 6-8, 6-7 | 15 | 4 min | 19 min |
| [25](lesson-25.md) | Did the Agent Improve—or Did the Numbers Move? | Significance, observability, ablations, and production evaluation | 6-3 evidence | 15 | 2 min | 17 min |

### Chapter 7

| Lesson | Problem-oriented title | Main learning outcome | Live anchor(s) | Slides | Demo | Target |
| ---: | --- | --- | --- | ---: | ---: | ---: |
| [26](lesson-26.md) | Why Does Model Training Happen in Three Stages? | Pre-training, SFT, RL, and the agent-environment loop | 7-1 | 15 | 2 min | 17 min |
| [27](lesson-27.md) | When Should You Teach with Examples—and When with Rewards? | SFT, loss masking, distribution shift, and the form-first rule | 7-4 evidence, 7-5 evidence | 15 | 4 min | 19 min |
| [28](lesson-28.md) | How Do Preferences Become a Trainable Signal? | RLHF, reward models, KL constraints, PPO, GRPO, and DPO | RL evaluation check | 15 | 2 min | 17 min |
| [29](lesson-29.md) | Why Do Data and Environments Matter More Than the Algorithm? | Practice grounds, task distributions, synthetic data, and fidelity | 7-9 data | 15 | 2 min | 17 min |
| [30](lesson-30.md) | How Do You Reward a Long Agent Trajectory? | Credit assignment, reward density, process signals, and path penalties | 7-14 gates | 15 | 2 min | 17 min |
| [31](lesson-31.md) | How Can a Model Learn to Use Tools with Fewer Samples? | Tool-call RL, sandbox feedback, distillation, and practical boundaries | 7-9 preflight | 15 | 2 min | 17 min |

### Chapter 8

| Lesson | Problem-oriented title | Main learning outcome | Live anchor(s) | Slides | Demo | Target |
| ---: | --- | --- | --- | ---: | ---: | ---: |
| [32](lesson-32.md) | How Do Failed Trajectories Become Learning Signals? | Outcome verification, process rules, Rubrics, and cross-trajectory experience | 8-1, 8-2 | 15 | 4 min | 19 min |
| [33](lesson-33.md) | Where Should an Agent Store What It Learns? | Knowledge, instructions, programs, parameters, and meta-updates | 8-4, Tool evolution | 15 | 4 min | 19 min |
| [34](lesson-34.md) | How Can a Self-Modifying Agent Change Without Drifting? | Candidate gates, transfer, retention, rollback, and sleep learning | 8-5, 8-6 | 15 | 4 min | 19 min |

### Chapter 9

| Lesson | Problem-oriented title | Main learning outcome | Live anchor(s) | Slides | Demo | Target |
| ---: | --- | --- | --- | ---: | ---: | ---: |
| [35](lesson-35.md) | Why Does a Voice Agent Feel Slow? | Cascaded pipelines, latency waterfalls, streaming, and turn detection | 9-1, 9-2 | 15 | 3 min | 18 min |
| [36](lesson-36.md) | When Should Voice Stop Taking Turns? | Omni, full-duplex interaction, fast-slow thinking, and controllable speech | 9-3, 9-4 | 15 | 4 min | 19 min |
| [37](lesson-37.md) | How Does an Agent Act Through Pixels? | GUI action spaces, visual grounding, and bounded interaction | 9-6 preflight, 9-6 retained status | 15 | 3 min | 18 min |
| [38](lesson-38.md) | How Does an Agent Turn Plans into Physical Actions? | Planning-control separation, VLA control, safety gates, and Sim2Real | 9-9 dry configuration, Robot safety gates | 15 | 3 min | 18 min |

### Chapter 10

| Lesson | Problem-oriented title | Main learning outcome | Live anchor(s) | Slides | Demo | Target |
| ---: | --- | --- | --- | ---: | ---: | ---: |
| [39](lesson-39.md) | When Should Agents Share the Same Context? | Shared trajectories, isolated contexts, role switching, and handoffs | 10-1, 10-2 | 15 | 2 min | 17 min |
| [40](lesson-40.md) | Who Should Coordinate Independent Agents? | Peer review, managers, decentralized handoffs, files, and control planes | 10-3 | 15 | 2 min | 17 min |
| [41](lesson-41.md) | When Is Multi-Agent Actually Better Than One Agent? | Information gain, parallelism, verification, budgets, and cost | 10-6 | 15 | 3 min | 18 min |
| [42](lesson-42.md) | How Do Agent Teams Fail—and What Should We Build Next? | Conflicts, error cascades, Agent societies, and the course synthesis | 10-8 offline diagnostic | 16 | 2 min | 18 min |


## Recording contract

- Speak in your own voice and add interpretation; the decks are visual prompts, not narration scripts.
- Run the listed commands in one contiguous terminal block after the explicit handoff slide.
- Treat preflights, validators, smoke checks, and dry configurations as scoped evidence—not completed long campaigns.
- Use the linked companion projects for experiments that are not demonstrated live.
- Demo-heavy lessons combine or remove conceptual slides so slide time plus terminal time stays within 20 minutes.
