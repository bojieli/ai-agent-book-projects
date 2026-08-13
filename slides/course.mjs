export const lessons = [
  {
    number: 1,
    chapter: "Introduction",
    part: "Orientation",
    title: "How Do We Replace Agent Intuition with Evidence?",
    subtitle: "A practice-first map of AI Agents in Depth",
    book: "Introduction; Book Structure; How to Read This Book",
    figure: "fig0-2.svg",
    figureAlt: "The four-part structure of the book",
    question: "Why do impressive Agent demos so often fail to become reliable products?",
    stakes: [
      ["Demo success", "One lucky trajectory proves possibility—not reliability."],
      ["Engineering judgment", "Every design choice needs a mechanism and a trade-off."],
      ["Scientific progress", "Without evaluation, change is indistinguishable from luck."]
    ],
    concepts: [
      ["Build", "Context, knowledge, tools, and code generation"],
      ["Improve", "Evaluation, post-training, and continual evolution"],
      ["Expand", "Voice, Computer Use, robotics, and collaboration"]
    ],
    contrast: {
      leftTitle: "Demo-driven",
      left: ["Start with a framework", "Celebrate one successful run", "Change prompts by intuition"],
      rightTitle: "Principle-driven",
      right: ["Start with a failure mode", "Run a controlled comparison", "Turn evidence into a design rule"],
      caption: "The course follows the right-hand loop."
    },
    code: {
      title: "The course's experimental loop",
      lang: "python",
      lines: [
        "question = define_failure_mode()",
        "hypothesis = predict_mechanism(question)",
        "evidence = run_controlled_experiment(hypothesis)",
        "rule = interpret(evidence, limitations=True)",
        "evaluate(rule)"
      ]
    },
    experiments: [
      {
        id: "Course tour",
        name: "Inspect one companion experiment before running it",
        duration: 1,
        command: "uv run python chapter1/context/main.py --help",
        watch: "Entry point, modes, providers, outputs, and reproducibility controls",
        mode: "Live terminal",
        path: "chapter1/context/"
      }
    ],
    findings: [
      "The book is organized around recurring engineering questions, not products.",
      "Experiments expose mechanisms through controls, ablations, and receipts.",
      "The author's interpretation—not terminal output alone—is the course's value."
    ],
    boundary: "A short lesson cannot reproduce every long-running campaign. It can make the protocol and evidence traceable.",
    rule: "Never present an Agent result without first stating what would count as success or failure.",
    extensions: [
      ["Learning paths", "docs/en/LEARNING.md"],
      ["Book prerequisites", "book-en/introduction.md"],
      ["Companion project index", "docs/en/README.md"]
    ],
    reflection: "Which Agent claim have you accepted after seeing only one successful run?",
    next: "Define an Agent by the interfaces that connect it to the world."
  },
  {
    number: 2,
    chapter: "Chapter 1",
    part: "Agent Fundamentals",
    title: "What Turns an LLM into an Agent?",
    subtitle: "Reasoning engine + working context + action interfaces",
    book: "Modern Agent = LLM + Context + Tools; Observation and Action Spaces",
    figure: "fig0-1.svg",
    figureAlt: "Agent equals LLM plus Context plus Tools",
    question: "What must be added to an LLM before it can pursue a goal in the world?",
    stakes: [
      ["LLM", "Chooses the next action from what it can currently see."],
      ["Context", "Defines the observation space and working state."],
      ["Tools", "Define the actions that can change the environment."]
    ],
    concepts: [
      ["Implementation", "LLM + Context + Tools"],
      ["Intuition", "Brain + eyes + hands and feet"],
      ["RL language", "Policy + observation space + action space"]
    ],
    contrast: {
      leftTitle: "Chat model",
      left: ["Produces text", "World state stays unchanged", "User drives every turn"],
      rightTitle: "Agent",
      right: ["Selects actions", "Observes tool results", "Continues until a stopping condition"],
      caption: "Agency comes from the loop and interfaces—not a new species of model."
    },
    code: {
      title: "The smallest useful abstraction",
      lang: "python",
      lines: [
        "observation = context.current_view()",
        "action = llm.choose(observation, tools)",
        "result = tools.execute(action)",
        "context.append(action, result)"
      ]
    },
    experiments: [
      {
        id: "1-2",
        name: "Watch a search Agent choose and use a tool",
        duration: 2,
        command: "uv run --extra ch1 python chapter1/web-search-agent/run_experiment_1_2.py --attempts 1 --timeout 120",
        watch: "Native tool calls, reasoning iterations, successful Formula Fibers, and acceptance checks",
        mode: "Live terminal",
        path: "chapter1/web-search-agent/"
      }
    ],
    findings: [
      "The model cannot act without an action interface.",
      "A tool result becomes the next observation.",
      "The same model can solve a new class of task when its interfaces expand."
    ],
    boundary: "A wider action space also increases security risk and the number of possible failures.",
    rule: "When an Agent cannot solve a task, first ask whether the missing capability belongs in the model, context, or tools.",
    extensions: [
      ["Experiment 1-3: search plus code generation", "chapter1/search-codegen/"],
      ["Three levels of capability updates", "book-en/images/fig1-1.svg"]
    ],
    reflection: "For a product you use, what are its observation and action spaces?",
    next: "Open the loop and identify every piece of information it depends on."
  },
  {
    number: 3,
    chapter: "Chapter 1",
    part: "Agent Fundamentals",
    title: "What Is Inside an Agent's Context?",
    subtitle: "Static prefix + dynamic trajectory",
    book: "Context: The Agent's Working Set; Experiment 1-1; The ReAct Loop",
    figure: "fig1-3.svg",
    figureAlt: "A ReAct trajectory for a multi-step task",
    question: "Which pieces of context are genuinely necessary—and what breaks when one disappears?",
    stakes: [
      ["Tool definitions", "Tell the model which actions exist."],
      ["Tool results", "Return environmental feedback."],
      ["Trajectory", "Preserves decisions, progress, and unresolved work."]
    ],
    concepts: [
      ["Static prefix", "System instructions + stable tool definitions"],
      ["Dynamic trajectory", "User, assistant, tool calls, and tool results"],
      ["ReAct", "Think → Act → Observe, repeated until verified"]
    ],
    contrast: {
      leftTitle: "Full context",
      left: ["Knows available tools", "Remembers completed steps", "Uses observations to advance"],
      rightTitle: "Ablated context",
      right: ["Cannot act", "Repeats work", "Contradicts or restarts"],
      caption: "Different missing components produce different failure signatures."
    },
    code: {
      title: "A production loop needs a budget",
      lang: "python",
      lines: [
        "for step in range(max_steps):",
        "    response = llm(messages, tools)",
        "    messages.append(response)",
        "    if response.is_final: break",
        "    messages.append(execute(response.tool_call))"
      ]
    },
    experiments: [
      {
        id: "1-1A",
        name: "Run the control and no-history arms",
        duration: 3,
        command: "uv run --extra ch1 python chapter1/context/main.py --mode ablation --provider kimi --ablation-modes full no_history --cases 1 --output /tmp/ch1-context-live.json",
        watch: "Iterations, tool-action counts, repeated calls, and whether the numerical answer appears",
        mode: "Live terminal",
        path: "chapter1/context/"
      },
      {
        id: "1-1B",
        name: "Inspect the accepted five-arm evidence",
        duration: 1,
        command: "jq '{evidence_mode, accepted:.analysis.experiment_execution_accepted, claims:.analysis.manuscript_behavior_claims, arms:[.arms[]|{mode,iterations,actions:.behavior.tool_action_count,repeated:.behavior.has_repeated_tool_action,correct:.behavior.canonical_answer_correct}]}' chapter1/context/validation/latest.json",
        watch: "Which predicted failures reproduced, and the negative no-reasoning result",
        mode: "Retained direct-API evidence",
        path: "chapter1/context/"
      }
    ],
    findings: [
      "Missing tool results commonly create repetition loops.",
      "Missing history makes the Agent restart completed work.",
      "A trajectory is executable state, not disposable chat text."
    ],
    boundary: "Keeping every token forever preserves history but eventually creates cost and retrieval problems.",
    rule: "Before compressing context, identify the state each message carries and the failure caused by losing it.",
    extensions: [
      ["Context ablation data", "extras/agent-lab/data/"],
      ["Experiment implementation", "chapter1/context/run_experiment_1_1.py"]
    ],
    reflection: "How would you detect a loop caused by missing or malformed tool feedback?",
    next: "Reliable completion requires engineering around the loop."
  },
  {
    number: 4,
    chapter: "Chapter 1",
    part: "Agent Fundamentals",
    title: "Why Doesn't a Stronger Model Make a Reliable Agent?",
    subtitle: "Harness engineering, orchestration, and guardrails",
    book: "Harness Engineering; Model Choice; Orchestration Patterns; Guardrails and Safety",
    figure: "fig1-5.svg",
    figureAlt: "The execution loop of an autonomous Agent",
    question: "If models keep improving, why does the software around them keep getting more important?",
    stakes: [
      ["Constrain", "Permissions, budgets, and valid action boundaries"],
      ["Verify", "Independent evidence that work is actually complete"],
      ["Recover", "Retries, fallbacks, checkpoints, and termination paths"]
    ],
    concepts: [
      ["Context engineering", "Control what the model can see."],
      ["Loop engineering", "Control when the system continues or stops."],
      ["Harness engineering", "Control the complete runtime around the model."]
    ],
    contrast: {
      leftTitle: "Workflow",
      left: ["Known stages", "Predictable control flow", "Easy to inspect"],
      rightTitle: "Autonomous Agent",
      right: ["Open-ended plan", "Adaptive tool use", "Needs stronger verification"],
      caption: "Use the least autonomous pattern that can solve the task."
    },
    code: {
      title: "Verification must observe the world",
      lang: "python",
      lines: [
        "proposal = agent.execute(task)",
        "evidence = environment.inspect(proposal)",
        "if not verifier.accepts(evidence):",
        "    agent.revise(evidence)",
        "guardrails.check_before_commit()"
      ]
    },
    experiments: [
      {
        id: "1-3",
        name: "Inspect a search-and-code execution plan",
        duration: 2,
        command: "uv run python chapter1/search-codegen/main.py --backend openai --dry-run --request \"Compare ASEAN capitals\"",
        watch: "Which work belongs to search, code, validation, and stopping logic",
        mode: "Live terminal",
        path: "chapter1/search-codegen/"
      }
    ],
    findings: [
      "Most production code handles boundaries and failures rather than the happy path.",
      "Independent observations add information that self-reflection cannot.",
      "Model selection should follow an evaluation, not a reputation."
    ],
    boundary: "A Harness can patch unstable behavior, but it cannot make an unverifiable goal objectively verifiable.",
    rule: "Prompts first, workflows second, autonomous Agents only where adaptation creates real value.",
    extensions: [
      ["Workflow patterns", "book-en/images/fig1-wf-routing.svg"],
      ["Evaluator-optimizer workflow", "book-en/images/fig1-wf-evaluator.svg"],
      ["n8n workflow example", "book-en/images/n8n-workflow.png"]
    ],
    reflection: "Which failure in your Agent should be prevented, detected, recovered, or escalated?",
    next: "Move inside the context window and inspect what the API actually sends."
  },
  {
    number: 5,
    chapter: "Chapter 2",
    part: "Context Engineering",
    title: "What Does the Model Actually See?",
    subtitle: "Messages, tool calls, and the Agent core loop",
    book: "Context: The Ceiling of Agent Capability; API-Level Context Structure",
    figure: "fig2-3.svg",
    figureAlt: "Message sequence for two tool calls",
    question: "When an Agent makes its third model call, what exactly is inside the request?",
    stakes: [
      ["Roles", "System, user, assistant, and tool messages have different semantics."],
      ["Ordering", "A tool result must follow the tool call it answers."],
      ["Composition", "Every call rebuilds a view from static and dynamic context."]
    ],
    concepts: [
      ["Context is a list", "Messages—not an abstract cloud of memory"],
      ["Tool call", "An assistant message proposing a structured action"],
      ["Tool result", "A new observation appended to the trajectory"]
    ],
    contrast: {
      leftTitle: "Single turn",
      left: ["One request", "One response", "No environmental feedback"],
      rightTitle: "Agent loop",
      right: ["Repeated requests", "Tool calls and results", "Growing trajectory"],
      caption: "The API structure is the runtime state machine."
    },
    code: {
      title: "Context at the API boundary",
      lang: "python",
      lines: [
        "messages = [{\"role\": \"user\", \"content\": task}]",
        "while True:",
        "    reply = client.responses.create(messages=messages, tools=tools)",
        "    messages.append(reply)",
        "    if reply.final: break",
        "    messages.append(run_tool(reply.tool_call))"
      ]
    },
    experiments: [
      {
        id: "2-1",
        name: "Run local tool calling and watch messages grow",
        duration: 3,
        command: "uv run python chapter2/local_llm_serving/main.py --backend ollama --mode single --task \"What is the weather in Tokyo?\"",
        watch: "Assistant tool call, tool result, and final answer",
        mode: "Live terminal",
        path: "chapter2/local_llm_serving/"
      }
    ],
    findings: [
      "The model only knows a tool exists because its schema is in context.",
      "Tool results are observations, not hidden side effects.",
      "A malformed message sequence changes the task state the model perceives."
    ],
    boundary: "Framework abstractions are convenient, but debugging requires inspecting raw API messages.",
    rule: "Log the exact message list and tool schemas for every reproducible Agent failure.",
    extensions: [
      ["Local serving benchmark", "chapter2/local_llm_serving/benchmark.py"],
      ["Minimal core loop", "book-en/chapter2.md"]
    ],
    reflection: "Which part of your Agent state exists outside the message list, and how is it reintroduced?",
    next: "Rearranging that list can change both latency and cost."
  },
  {
    number: 6,
    chapter: "Chapter 2",
    part: "Context Engineering",
    title: "Why Can One Timestamp Make an Agent Slow?",
    subtitle: "Chat templates, attention, KV Cache, and stable prefixes",
    book: "KV Cache-Friendly Context Design; Chat Template; Prompt Cache",
    figure: "fig2-10.svg",
    figureAlt: "KV Cache prefix reuse",
    question: "Why can a harmless dynamic line near the top of the prompt invalidate most cached computation?",
    stakes: [
      ["Token stream", "Message objects become one ordered sequence."],
      ["Prefix reuse", "Matching early tokens reuse previous attention work."],
      ["Architecture", "Dynamic content placement becomes a systems decision."]
    ],
    concepts: [
      ["KV Cache", "Reuses keys and values within inference"],
      ["Prompt Cache", "Reuses a stable prefix across API requests"],
      ["Stable prefix", "Instructions and tools that do not change turn to turn"]
    ],
    contrast: {
      leftTitle: "Cache-friendly",
      left: ["Stable system prompt", "Stable tool order", "Dynamic state appended late"],
      rightTitle: "Cache-breaking",
      right: ["Timestamp near the front", "Randomized tool order", "Reformatted history"],
      caption: "One early mismatch invalidates everything that follows."
    },
    code: {
      title: "Move changing state after the stable prefix",
      lang: "python",
      lines: [
        "static = [system_prompt, stable_tool_schemas]",
        "trajectory = load_messages(session_id)",
        "status = make_dynamic_status(now, progress)",
        "messages = static + trajectory + [status]"
      ]
    },
    experiments: [
      {
        id: "2-3",
        name: "Compare context-management cache reports",
        duration: 2,
        command: "uv run python chapter2/kv-cache/main.py --report",
        watch: "Prefix hits, recomputation, repeated work, and estimated cost",
        mode: "Live terminal",
        path: "chapter2/kv-cache/"
      },
      {
        id: "2-2",
        name: "Generate a small attention view",
        duration: 2,
        command: "uv run python chapter2/attention_visualization/attention_cli.py --prompt \"Explain attention in one sentence.\" --output attention.png",
        watch: "A token's weighted access to earlier tokens",
        mode: "Live terminal",
        path: "chapter2/attention_visualization/"
      }
    ],
    findings: [
      "The API's message abstraction hides an ordered token prefix.",
      "Cache efficiency depends on exact prefix stability.",
      "Correct context management can improve quality and latency together."
    ],
    boundary: "Cache-friendly does not mean never editing context; it means making edits deliberate and localized.",
    rule: "Place stable, frequently reused information first and dynamic information as late as its semantics allow.",
    extensions: [
      ["Attention heatmap", "book-en/images/fig2-7.png"],
      ["Chat-template token structure", "book-en/images/fig2-8.svg"],
      ["Editable and composable notes", "book-en/chapter2.md"]
    ],
    reflection: "Which dynamic values in your system prompt silently destroy prefix reuse?",
    next: "Even a perfectly cached prompt can fail if its instructions are poorly organized."
  },
  {
    number: 7,
    chapter: "Chapter 2",
    part: "Context Engineering",
    title: "Why Do Better Prompts Need Structure, Not More Rules?",
    subtitle: "Process-oriented instructions, tool definitions, and injection boundaries",
    book: "Prompt Engineering; Tool Definition Design; Prompt Injection",
    figure: "fig2-1.svg",
    figureAlt: "Composition of an Agent context window",
    question: "Why can adding correct business rules make an Agent less reliable?",
    stakes: [
      ["Organization", "The model must retrieve the right instruction at the right step."],
      ["Execution", "Rules should map to observable decisions and actions."],
      ["Trust", "Untrusted content must never inherit instruction authority."]
    ],
    concepts: [
      ["Behavioral frame", "Tone and role set defaults—not guarantees"],
      ["Process prompt", "Organize instructions around a task flow"],
      ["Layered defense", "Prompt hardening + source boundaries + tool checks"]
    ],
    contrast: {
      leftTitle: "Rule stack",
      left: ["Appended over time", "Conflicting priorities", "Hard to retrieve"],
      rightTitle: "Executable process",
      right: ["Ordered stages", "Explicit conditions", "Observable outputs"],
      caption: "Prompt quality depends on information architecture."
    },
    code: {
      title: "Treat retrieved content as data",
      lang: "python",
      lines: [
        "content = web.read(url)",
        "context.append({",
        "  \"role\": \"tool\",",
        "  \"content\": tag_untrusted(content)",
        "})",
        "policy.check(proposed_action)"
      ]
    },
    experiments: [
      {
        id: "2-4",
        name: "Inspect prompt-ablation results",
        duration: 2,
        command: "uv run python chapter2/prompt-engineering/analyze_results.py --output prompt-summary.json",
        watch: "Effect of organization, tone, examples, and tool descriptions",
        mode: "Live terminal",
        path: "chapter2/prompt-engineering/"
      },
      {
        id: "2-5",
        name: "Compare an indirect injection with layered defense",
        duration: 3,
        command: "uv run python chapter2/prompt-injection/demo.py -n 1 -a 2 -d 1,4",
        watch: "Attack success with no defense versus combined defense",
        mode: "Live terminal",
        path: "chapter2/prompt-injection/"
      }
    ],
    findings: [
      "Disorganized correct rules can underperform a shorter process prompt.",
      "Tool descriptions shape both action selection and argument quality.",
      "Prompts reduce attacks but cannot form the final security boundary."
    ],
    boundary: "No system prompt can safely authorize irreversible actions using facts supplied only by the model.",
    rule: "Translate business policy into a process, then enforce critical invariants outside the model.",
    extensions: [
      ["Full prompt-ablation campaign", "chapter2/prompt-engineering/"],
      ["All injection scenarios and defenses", "chapter2/prompt-injection/"]
    ],
    reflection: "Which sentence in your system prompt should instead be a tool-side invariant?",
    next: "Keep specialist instructions out of the prompt until the task actually needs them."
  },
  {
    number: 8,
    chapter: "Chapter 2",
    part: "Context Engineering",
    title: "How Can an Agent Know What It Needs to Learn?",
    subtitle: "Skills, progressive disclosure, and on-demand capability",
    book: "Dynamic Prompts and Agent Skills; Skills and Tools",
    figure: "fig2-11.svg",
    figureAlt: "Skills progressive disclosure",
    question: "How can an Agent access hundreds of specialist procedures without carrying all of them in every prompt?",
    stakes: [
      ["Discovery", "A thin index tells the Agent what knowledge exists."],
      ["Disclosure", "Detailed instructions load only after a relevant trigger."],
      ["Execution", "Bundled scripts make repeated procedures deterministic."]
    ],
    concepts: [
      ["Skill metadata", "Name and description stay visible"],
      ["Skill body", "Workflow loads only when selected"],
      ["Resources", "References and scripts load only when required"]
    ],
    contrast: {
      leftTitle: "Everything preloaded",
      left: ["Large static prompt", "High information competition", "Every task pays the cost"],
      rightTitle: "Progressive disclosure",
      right: ["Thin capability index", "On-demand instructions", "Task-specific context"],
      caption: "Skills trade metacognition risk for context efficiency."
    },
    code: {
      title: "A Skill is a navigable package",
      lang: "text",
      lines: [
        "pptx/",
        "├── SKILL.md          # when and how",
        "├── reference.md      # details on demand",
        "├── scripts/",
        "│   └── render.py",
        "└── templates/"
      ]
    },
    experiments: [
      {
        id: "2-6",
        name: "Generate a deck through progressive Skill loading",
        duration: 3,
        command: "uv run python chapter2/agent-skills-ppt/demo.py --offline",
        watch: "Metadata → Skill body → referenced script → verified artifact",
        mode: "Live terminal",
        path: "chapter2/agent-skills-ppt/"
      }
    ],
    findings: [
      "The Agent initially sees a capability index rather than full instructions.",
      "File reads turn specialist knowledge into explicit trajectory events.",
      "Scripts reduce token use and make artifact creation testable."
    ],
    boundary: "Progressive disclosure fails when the model does not recognize that a Skill is relevant.",
    rule: "Keep capability descriptions broad enough for discovery and Skill bodies narrow enough for reliable execution.",
    extensions: [
      ["Official Skill runtime paths", "chapter2/agent-skills-ppt/run_official_experiment.py"],
      ["Skill-enabled trajectory", "book-en/images/fig2-12.svg"],
      ["Skills versus tools", "book-en/chapter2.md"]
    ],
    reflection: "How would you measure false-negative Skill discovery?",
    next: "Long tasks need explicit state and selective forgetting, not only selective loading."
  },
  {
    number: 9,
    chapter: "Chapter 2",
    part: "Context Engineering",
    title: "How Can an Agent Stay Oriented in a Long Task?",
    subtitle: "Status bars, physical time, context rot, and compression",
    book: "Agent Status Bar; Context Compression; Isolation Over Compression",
    figure: "fig2-16.svg",
    figureAlt: "Comparison of context compression strategies",
    question: "Why does an Agent lose track of progress even before its context window is full?",
    stakes: [
      ["Context rot", "Relevant facts remain present but become hard to retrieve."],
      ["Implicit state", "Progress and time are scattered across the trajectory."],
      ["Compression", "Raw history must become high-density working state."]
    ],
    concepts: [
      ["Status bar", "Explicit task, time, budget, and progress state"],
      ["Hierarchical compression", "Preserve recent detail and summarize older phases"],
      ["Isolation", "Move independent work into separate contexts"]
    ],
    contrast: {
      leftTitle: "Long raw trajectory",
      left: ["Repeated observations", "Low information density", "Reasoning cost grows"],
      rightTitle: "Engineered working set",
      right: ["Explicit current state", "Compressed completed phases", "Isolated sub-tasks"],
      caption: "The goal is usable information—not maximum token retention."
    },
    code: {
      title: "Make hidden state explicit",
      lang: "python",
      lines: [
        "status = {",
        "  \"goal\": task.goal,",
        "  \"done\": completed_steps,",
        "  \"budget\": remaining_steps,",
        "  \"elapsed\": clock.elapsed()",
        "}"
      ]
    },
    experiments: [
      {
        id: "2-8",
        name: "Preview the injected status information",
        duration: 1,
        command: "uv run python chapter2/system-hint/main.py --mode preview",
        watch: "Task progress, time, tool count, and remaining budget",
        mode: "Live terminal",
        path: "chapter2/system-hint/"
      },
      {
        id: "2-9",
        name: "Compare compression strategies",
        duration: 3,
        command: "uv run python chapter2/context-compression/experiment.py --list-strategies",
        watch: "What each strategy preserves, discards, and recomputes",
        mode: "Live terminal",
        path: "chapter2/context-compression/"
      }
    ],
    findings: [
      "A status bar turns repeated inference into direct retrieval.",
      "Compression is needed for information density before token overflow.",
      "Independent sub-tasks are often better isolated than summarized."
    ],
    boundary: "An incorrect status bar can be more harmful than missing meta-information because the Agent trusts it.",
    rule: "Compress completed history into verifiable state; keep recent evidence available; isolate independent work.",
    extensions: [
      ["Experiment 2-7: status-bar attention", "chapter2/attention_visualization/run_status_bar_experiment.py"],
      ["Run all six compression strategies", "chapter2/context-compression/run_all_strategies.py"],
      ["Status insertion position", "book-en/images/fig2-15.svg"],
      ["Compression processing flow", "book-en/images/fig2-17.svg"]
    ],
    reflection: "Which fields in a status bar can be computed deterministically instead of inferred by the model?",
    next: "Extend working context across sessions without turning memory into noise."
  },
  {
    number: 10,
    chapter: "Chapter 3",
    part: "Memory and Knowledge",
    title: "What Should an Agent Remember About a User?",
    subtitle: "Memory levels, representations, evaluation, and privacy",
    book: "User Memory System; Three-Level Framework; Four Storage Formats; Privacy",
    figure: "fig3-2.svg",
    figureAlt: "Four strategies for representing user memory",
    question: "How do we preserve useful preferences without turning every past action into a permanent fact?",
    stakes: [
      ["Recall", "Recover an explicit fact from a previous session."],
      ["Cross-session reasoning", "Combine evidence from several interactions."],
      ["Proactive service", "Notice a relevant need before the user repeats it."]
    ],
    concepts: [
      ["Simple Notes", "Atomic facts with little context"],
      ["JSON Cards", "Structured facts with evidence and scope"],
      ["Advanced Cards", "Conflicts, confidence, time, and applicability"]
    ],
    contrast: {
      leftTitle: "Store everything",
      left: ["High noise", "Privacy exposure", "Contradictory details"],
      rightTitle: "Managed memory",
      right: ["Evidence-backed entries", "Conflict resolution", "Retention and sanitization"],
      caption: "Memory is a governed knowledge system, not a transcript archive."
    },
    code: {
      title: "A memory needs provenance",
      lang: "json",
      lines: [
        "{",
        "  \"fact\": \"Prefers aisle seats\",",
        "  \"scope\": \"long-haul flights\",",
        "  \"evidence\": [\"session-18:turn-9\"],",
        "  \"confidence\": 0.82,",
        "  \"updated_at\": \"2026-08-03\"",
        "}"
      ]
    },
    experiments: [
      {
        id: "3-1/3-2",
        name: "Compare user-memory representations",
        duration: 3,
        command: "uv run python chapter3/user-memory/main.py --mode demo --memory-mode advanced_json_cards",
        watch: "What is extracted, how context is preserved, and how conflicts appear",
        mode: "Live terminal",
        path: "chapter3/user-memory/"
      },
      {
        id: "3-3",
        name: "Sanitize a memory-bearing log",
        duration: 2,
        command: "uv run python chapter3/log-sanitization/main.py --demo",
        watch: "Secrets removed while diagnostic structure remains",
        mode: "Live terminal",
        path: "chapter3/log-sanitization/"
      }
    ],
    findings: [
      "Memory quality must be evaluated at several capability levels.",
      "Structured representations retain scope and provenance better than flat notes.",
      "Privacy controls belong in the ingestion path, before persistence."
    ],
    boundary: "A detailed schema improves precision but increases extraction cost and schema-maintenance burden.",
    rule: "Store the minimum durable claim together with evidence, scope, confidence, and time.",
    extensions: [
      ["Memory evaluation suite", "chapter3/user-memory-evaluation/"],
      ["Mem0 comparison", "chapter3/mem0/"],
      ["Memobase comparison", "chapter3/memobase/"],
      ["Multi-type memory architecture", "book-en/images/fig3-4.svg"]
    ],
    reflection: "How should a memory system respond when a newer statement contradicts an older one?",
    next: "Retrieve external knowledge when exact words and semantic similarity disagree."
  },
  {
    number: 11,
    chapter: "Chapter 3",
    part: "Memory and Knowledge",
    title: "Why Does Semantic Search Miss Exact Answers?",
    subtitle: "Chunking, dense retrieval, sparse retrieval, and evaluation",
    book: "RAG Basics; Document Chunking; Dense Embeddings; Sparse Embeddings",
    figure: "fig3-8.svg",
    figureAlt: "BM25 scoring mechanism for exact lexical retrieval",
    question: "Why can a vector search understand a topic yet miss the exact identifier the user needs?",
    stakes: [
      ["Chunking", "Defines the atomic units that can be found."],
      ["Dense retrieval", "Matches meaning and paraphrase."],
      ["Sparse retrieval", "Matches exact words, numbers, and identifiers."]
    ],
    concepts: [
      ["Recall@k", "Did the relevant item enter the candidate set?"],
      ["ANN index", "Trade exact search for speed and memory"],
      ["BM25", "Weight exact terms with saturation and length normalization"]
    ],
    contrast: {
      leftTitle: "Dense",
      left: ["Semantic similarity", "Handles paraphrases", "May miss rare identifiers"],
      rightTitle: "Sparse",
      right: ["Exact lexical match", "Transparent term scores", "Misses synonyms"],
      caption: "The failure modes are complementary."
    },
    code: {
      title: "Measure retrieval before generation",
      lang: "python",
      lines: [
        "candidates = index.search(query, k=10)",
        "recall = any(doc.id in relevant_ids for doc in candidates)",
        "for rank, doc in enumerate(candidates, 1):",
        "    print(rank, doc.score, doc.id)"
      ]
    },
    experiments: [
      {
        id: "3-4",
        name: "Compare ANN index behavior",
        duration: 2,
        command: "uv run python chapter3/dense-embedding/cli.py --compare-ann -k 10",
        watch: "Latency, recall, memory, and incremental-update trade-offs",
        mode: "Live terminal",
        path: "chapter3/dense-embedding/"
      },
      {
        id: "3-5",
        name: "Explain one BM25 score",
        duration: 2,
        command: "uv run python chapter3/sparse-embedding/cli.py -q \"model distillation\" --explain",
        watch: "Per-term TF, IDF, saturation, and length effects",
        mode: "Live terminal",
        path: "chapter3/sparse-embedding/"
      }
    ],
    findings: [
      "A retrieval failure can begin at chunk boundaries rather than the model.",
      "ANN algorithms differ in update behavior as well as speed.",
      "Exact and semantic search solve different parts of the problem."
    ],
    boundary: "A higher retrieval score does not prove that the retrieved passage answers the question.",
    rule: "Evaluate the candidate set independently before asking whether generation is good.",
    extensions: [
      ["HNSW structure", "book-en/images/fig3-7.svg"],
      ["BM25 implementation", "chapter3/sparse-embedding/"],
      ["Dense model comparison", "chapter3/dense-embedding/"]
    ],
    reflection: "Which queries in your domain are dominated by identifiers rather than semantics?",
    next: "Fuse complementary retrievers, then organize knowledge beyond flat chunks."
  },
  {
    number: 12,
    chapter: "Chapter 3",
    part: "Memory and Knowledge",
    title: "Why Is One Retrieval Index Never Enough?",
    subtitle: "Hybrid search, reranking, multimodality, and structured knowledge",
    book: "Hybrid Retrieval; Multimodal Extraction; Structured Indexing; Filesystem Paradigm",
    figure: "fig3-9.svg",
    figureAlt: "Hybrid retrieval and reranking pipeline",
    question: "How do we combine complementary retrieval signals without letting one score dominate?",
    stakes: [
      ["Candidate fusion", "Merge dense and sparse result sets."],
      ["Reranking", "Use a stronger model only on a small candidate pool."],
      ["Knowledge shape", "Trees, graphs, files, images, and tables preserve different structure."]
    ],
    concepts: [
      ["Hybrid retrieval", "Broad recall from multiple retrievers"],
      ["Neural reranker", "More precise ordering at higher per-item cost"],
      ["Structured index", "Represent hierarchy or relationships explicitly"]
    ],
    contrast: {
      leftTitle: "Flat chunks",
      left: ["Simple ingestion", "Local passage questions", "Weak global structure"],
      rightTitle: "Structured knowledge",
      right: ["Hierarchies and graphs", "Multi-hop questions", "More governance cost"],
      caption: "Choose an index for the questions—not for fashion."
    },
    code: {
      title: "Fuse ranks before reranking",
      lang: "python",
      lines: [
        "dense = dense_index.search(query, k=20)",
        "sparse = bm25.search(query, k=20)",
        "pool = reciprocal_rank_fusion(dense, sparse)",
        "answer_context = reranker.top(query, pool, k=5)"
      ]
    },
    experiments: [
      {
        id: "3-6",
        name: "Expose every retrieval stage",
        duration: 3,
        command: "uv run python chapter3/retrieval-pipeline/evaluate.py --query \"XR-7003\"",
        watch: "Dense candidates, sparse candidates, fusion, reranking, and final rank",
        mode: "Live terminal",
        path: "chapter3/retrieval-pipeline/"
      },
      {
        id: "3-7",
        name: "Compare RAPTOR and GraphRAG",
        duration: 2,
        command: "uv run python chapter3/structured-index/main.py demo",
        watch: "Questions favored by hierarchical summaries versus relationship graphs",
        mode: "Live terminal",
        path: "chapter3/structured-index/"
      }
    ],
    findings: [
      "Hybrid retrieval improves recall because its component failures differ.",
      "Reranking spends expensive reasoning on a small, diverse pool.",
      "Structured indexes help only when queries need their encoded structure."
    ],
    boundary: "More stages increase latency, operational cost, and the number of components that can drift.",
    rule: "Add a retrieval stage only when an evaluation identifies the failure it corrects.",
    extensions: [
      ["Experiment 4-2: multimodal strategies", "chapter4/multimodal-agent/"],
      ["RAPTOR tree", "book-en/images/fig3-10.svg"],
      ["GraphRAG graph", "book-en/images/fig3-11.svg"],
      ["Knowledge-base governance", "book-en/chapter3.md"]
    ],
    reflection: "Which query type would reveal that your flat index has lost document structure?",
    next: "Let the Agent decide whether another retrieval step is necessary."
  },
  {
    number: 13,
    chapter: "Chapter 3",
    part: "Memory and Knowledge",
    title: "When Should the Agent Decide What to Retrieve?",
    subtitle: "Agentic RAG, contextual retrieval, and two-tier memory",
    book: "Agentic RAG; Contextual Retrieval; Deep Knowledge Extraction",
    figure: "fig3-13.svg",
    figureAlt: "Agentic RAG architecture",
    question: "When is a fixed retrieve-once pipeline insufficient for a question?",
    stakes: [
      ["Search decision", "The Agent decides whether retrieval is needed."],
      ["Query reformulation", "New evidence changes the next search."],
      ["Stopping", "The Agent judges whether evidence is sufficient."]
    ],
    concepts: [
      ["Agentic RAG", "Retrieval becomes a tool inside ReAct"],
      ["Contextual retrieval", "Restore document context before indexing each chunk"],
      ["Two-tier memory", "Resident overview + retrieved detail"]
    ],
    contrast: {
      leftTitle: "Retrieve once",
      left: ["Fixed query", "Fixed top-k", "One chance to find evidence"],
      rightTitle: "Agentic retrieval",
      right: ["Iterative queries", "Evidence-aware decisions", "Explicit stopping"],
      caption: "Autonomy adds flexibility and a new metacognition failure mode."
    },
    code: {
      title: "Retrieval becomes an action",
      lang: "python",
      lines: [
        "while not evidence_sufficient(context):",
        "    query = agent.formulate_search(context)",
        "    passages = search(query)",
        "    context.add(passages)",
        "return agent.answer_with_citations(context)"
      ]
    },
    experiments: [
      {
        id: "3-8",
        name: "Compare fixed and Agentic RAG offline",
        duration: 2,
        command: "uv run python chapter3/agentic-rag/compare_offline.py",
        watch: "Query count, evidence coverage, answer quality, and cost",
        mode: "Live terminal",
        path: "chapter3/agentic-rag/"
      },
      {
        id: "3-10",
        name: "Compare plain and contextual chunks",
        duration: 2,
        command: "uv run python chapter3/contextual-retrieval/compare_retrieval.py --per-query",
        watch: "Failures repaired by adding document-level context",
        mode: "Live terminal",
        path: "chapter3/contextual-retrieval/"
      },
      {
        id: "3-11",
        name: "Compare two-tier user memory",
        duration: 2,
        command: "uv run python chapter3/contextual-retrieval-for-user-memory/contextual_compare.py",
        watch: "Resident overview plus on-demand conversation detail",
        mode: "Live terminal",
        path: "chapter3/contextual-retrieval-for-user-memory/"
      }
    ],
    findings: [
      "Iterative retrieval helps when later queries depend on earlier evidence.",
      "Contextual prefixes repair semantic loss introduced by chunking.",
      "Overview and detail require different storage and access strategies."
    ],
    boundary: "An Agent cannot retrieve what it does not realize it is missing.",
    rule: "Use Agentic retrieval for genuinely multi-step evidence gathering; keep simple questions on a simple path.",
    extensions: [
      ["Experiment 3-9: Agentic RAG for memory", "chapter3/agentic-rag-for-user-memory/"],
      ["Experiment 3-12: structured knowledge extraction", "chapter3/structured-knowledge-extraction/"],
      ["Contextual retrieval diagram", "book-en/images/fig3-14.svg"],
      ["Knowledge extraction pipeline", "book-en/images/fig3-15.svg"]
    ],
    reflection: "What independent signal can tell an Agent that its evidence is insufficient?",
    next: "Turn knowledge into actions through carefully designed tools."
  },
  {
    number: 14,
    chapter: "Chapter 4",
    part: "Tools",
    title: "What Makes a Tool Easy for a Model to Use?",
    subtitle: "Capability boundaries, granularity, descriptions, and MCP",
    book: "Tool Classification; Universal Principles; MCP; Perception Tools",
    figure: "fig4-1.svg",
    figureAlt: "MCP protocol interaction sequence",
    question: "Why can two tools expose the same capability yet produce very different Agent behavior?",
    stakes: [
      ["Granularity", "One broad tool or several composable operations?"],
      ["Description", "The model selects tools from names, schemas, and examples."],
      ["Fidelity", "Arguments must preserve the user's intended operation."]
    ],
    concepts: [
      ["Perception", "Read the world without changing it"],
      ["Execution", "Change state and create consequences"],
      ["Collaboration", "Reach another Agent or human"]
    ],
    contrast: {
      leftTitle: "Dedicated tool",
      left: ["Clear intent", "Narrow schema", "Many definitions at scale"],
      rightTitle: "Skill + executor",
      right: ["General action surface", "Instructions on demand", "Needs stronger sandboxing"],
      caption: "Capability expression is a design choice."
    },
    code: {
      title: "A schema is an Agent-facing API",
      lang: "json",
      lines: [
        "{",
        "  \"name\": \"weather\",",
        "  \"description\": \"Current observed weather for one place\",",
        "  \"parameters\": {\"city\": {\"type\": \"string\"}},",
        "  \"required\": [\"city\"]",
        "}"
      ]
    },
    experiments: [
      {
        id: "4-1",
        name: "Discover and call perception tools",
        duration: 3,
        command: "uv run python chapter4/perception-tools/cli.py demo --offline",
        watch: "Tool discovery, typed arguments, truncation, and evidence returned",
        mode: "Live terminal",
        path: "chapter4/perception-tools/"
      }
    ],
    findings: [
      "Read-only tools are easier to cache, parallelize, and trust.",
      "Descriptions should state scope, provenance, and failure behavior.",
      "MCP standardizes interoperability but not tool quality."
    ],
    boundary: "Every third-party server creates a new trust boundary for descriptions, credentials, and returned content.",
    rule: "Design tools for faithful action and inspectable evidence before optimizing convenience.",
    extensions: [
      ["MCP server implementation", "chapter4/perception-tools/"],
      ["Container deployment", "chapter4/DOCKER_DEPLOYMENT.md"],
      ["Tool taxonomy", "book-en/chapter4.md"]
    ],
    reflection: "Which parameter in your tool can silently change the meaning of the user's request?",
    next: "Add execution power without letting a model become the security boundary."
  },
  {
    number: 15,
    chapter: "Chapter 4",
    part: "Tools",
    title: "How Do You Let an Agent Act Without Letting It Cause Damage?",
    subtitle: "Execution tools, independent checks, and fail-closed design",
    book: "Execution Tools; Security; Proposer-Reviewer; Sidecar",
    figure: "fig4-5.svg",
    figureAlt: "Synchronous model training versus asynchronous deployment",
    question: "Where should safety checks live when the model can write files, run code, and call external systems?",
    stakes: [
      ["Risk classification", "Read, reversible write, irreversible action"],
      ["Pre-approval", "Review intent and parameters before execution"],
      ["Post-validation", "Inspect the actual resulting state"]
    ],
    concepts: [
      ["Fail closed", "Unknown or malformed operations are denied"],
      ["Independent evidence", "Use data the proposer cannot forge"],
      ["Sidecar", "Keep enforcement outside the Agent's own mutable process"]
    ],
    contrast: {
      leftTitle: "Model self-report",
      left: ["Claims an action is safe", "Can hallucinate facts", "Shares the same compromised context"],
      rightTitle: "Independent gate",
      right: ["Reads server truth", "Enforces deterministic invariants", "Logs the decision"],
      caption: "The final boundary must not trust the model's own claim."
    },
    code: {
      title: "Server truth is the gatekeeper",
      lang: "python",
      lines: [
        "request = agent.propose_action()",
        "facts = database.read_ground_truth(request.target)",
        "policy.validate(request, facts)",
        "result = executor.run(request)",
        "validator.inspect(result)"
      ]
    },
    experiments: [
      {
        id: "4-3A",
        name: "Run an allowed code action",
        duration: 1,
        command: "uv run python chapter4/execution-tools/cli.py code --language python --code \"print(2 ** 10)\"",
        watch: "Validation, sandbox execution, and bounded output",
        mode: "Live terminal",
        path: "chapter4/execution-tools/"
      },
      {
        id: "4-3B",
        name: "Inspect execution-tool safety behavior",
        duration: 2,
        command: "uv run python chapter4/execution-tools/cli.py demo",
        watch: "Approval, rejection, syntax checks, and output handling",
        mode: "Live terminal",
        path: "chapter4/execution-tools/"
      }
    ],
    findings: [
      "Risk depends on parameters and environment, not only the tool name.",
      "Pre-approval reduces harmful attempts; validation catches harmful results.",
      "Long outputs need truncation plus durable storage, not silent loss."
    ],
    boundary: "A second model is not independent if it sees the same injected context and trusts the same unverified facts.",
    rule: "Guide the model with instructions, but enforce irreversible constraints with independent code and data.",
    extensions: [
      ["Execution-tool tests", "chapter4/execution-tools/"],
      ["Sidecar design", "book-en/chapter4.md"]
    ],
    reflection: "What is the trusted root in your Agent system, and can the Agent modify it?",
    next: "Some tasks require another Agent or a human rather than another tool."
  },
  {
    number: 16,
    chapter: "Chapter 4",
    part: "Tools",
    title: "When Should an Agent Ask for Help or Delegate?",
    subtitle: "Sub-agents, Human-in-the-Loop, and communication tools",
    book: "Collaboration Tools; User Communication; Virtual Identity",
    figure: "fig4-2.svg",
    figureAlt: "Event-driven asynchronous Agent architecture",
    question: "How should an Agent hand work to another actor without losing context or control?",
    stakes: [
      ["Handoff", "Pass only the facts and artifacts the collaborator needs."],
      ["Lifecycle", "Spawn, message, query, cancel, and collect results."],
      ["Escalation", "Ask a human when authority or missing judgment requires it."]
    ],
    concepts: [
      ["Minimal handoff", "Task parameters with almost no history"],
      ["Distilled handoff", "Facts, constraints, artifacts, and open questions"],
      ["HITL", "A permission and information channel—not an error screen"]
    ],
    contrast: {
      leftTitle: "Full transcript",
      left: ["Maximum context", "Large and biasing", "Leaks irrelevant information"],
      rightTitle: "Handoff package",
      right: ["Confirmed facts", "Artifact paths", "Explicit responsibility"],
      caption: "Context sharing and delegation are separate design decisions."
    },
    code: {
      title: "Lifecycle primitives stay small",
      lang: "python",
      lines: [
        "worker = spawn_subagent(task, context=handoff)",
        "send_message(worker, update)",
        "status = get_status(worker)",
        "if no_longer_needed(status):",
        "    cancel_subagent(worker)"
      ]
    },
    experiments: [
      {
        id: "4-4A",
        name: "Compare sub-agent handoff strategies",
        duration: 2,
        command: "uv run python chapter4/collaboration-tools/main.py subagent compare",
        watch: "Context size, task completeness, and irrelevant carryover",
        mode: "Live terminal",
        path: "chapter4/collaboration-tools/"
      },
      {
        id: "4-4B",
        name: "Exercise a Human-in-the-Loop gate",
        duration: 1,
        command: "uv run python chapter4/collaboration-tools/main.py hitl approve --message \"Delete 1000 records?\" --timeout 5 --auto-approve",
        watch: "Pending state, timeout, approval, and audit record",
        mode: "Live terminal",
        path: "chapter4/collaboration-tools/"
      }
    ],
    findings: [
      "A collaborator should receive a task contract, not indiscriminate history.",
      "Cancellation and status are first-class parts of delegation.",
      "Human intervention works best when the Agent explains the decision and safe defaults."
    ],
    boundary: "A slow or unavailable human cannot be treated as a synchronous function call.",
    rule: "Design collaboration as an asynchronous lifecycle with explicit authority and structured handoffs.",
    extensions: [
      ["Multi-channel notifications", "chapter4/collaboration-tools/"],
      ["Timers and delayed tasks", "chapter4/collaboration-tools/"],
      ["Sub-agent comparison script", "chapter4/collaboration-tools/subagent_comparison.py"]
    ],
    reflection: "What should the Agent do safely while waiting for a user's decision?",
    next: "Allow events to arrive while the Agent is already working."
  },
  {
    number: 17,
    chapter: "Chapter 4",
    part: "Tools",
    title: "How Can a Synchronous Model Live in an Asynchronous World?",
    subtitle: "Events, interruption, parallelism, and proactive tool discovery",
    book: "Event-Driven Asynchronous Agents; Proactive Tool Discovery",
    figure: "fig4-3.svg",
    figureAlt: "Three asynchronous event-processing strategies",
    question: "What happens when an urgent event arrives while a tool call is still running?",
    stakes: [
      ["Ingress", "External events can wake the Agent."],
      ["Scheduling", "Queue, interrupt, or parallelize by urgency."],
      ["Discovery", "Find a capability without loading every schema."]
    ],
    concepts: [
      ["Event queue", "Durable arrival, priority, and replay"],
      ["Cancellation", "Stop work safely and preserve recoverable state"],
      ["Meta-tool", "Search a large tool catalog on demand"]
    ],
    contrast: {
      leftTitle: "Synchronous loop",
      left: ["One request at a time", "No mid-turn updates", "Tool latency blocks attention"],
      rightTitle: "Async Harness",
      right: ["Inbox and scheduler", "Interrupt or parallel policy", "Checkpoints and notifications"],
      caption: "The model remains turn-based; the Harness absorbs real-world concurrency."
    },
    code: {
      title: "Events need an explicit policy",
      lang: "python",
      lines: [
        "event = await inbox.get()",
        "match event.urgency:",
        "    case \"interrupt\": await cancel(current_task)",
        "    case \"immediate\": spawn(event)",
        "    case _: queue.append(event)"
      ]
    },
    experiments: [
      {
        id: "4-5",
        name: "Trigger a timed event",
        duration: 2,
        command: "uv run python chapter4/agent-with-event-trigger/event_loop_demo.py --mock --trigger timer --delay 2 --duration 6",
        watch: "Registration, event arrival, processing, and delivery",
        mode: "Live terminal",
        path: "chapter4/agent-with-event-trigger/"
      },
      {
        id: "4-6",
        name: "Interrupt and recover a long-running task",
        duration: 2,
        command: "uv run python chapter4/async-agent/demo.py interrupt",
        watch: "Cancellation point, cleanup, checkpoint, and recovery",
        mode: "Live terminal",
        path: "chapter4/async-agent/"
      },
      {
        id: "4-7",
        name: "Discover tools instead of injecting the catalog",
        duration: 2,
        command: "uv run python chapter4/active-tool-discovery/demo.py --offline",
        watch: "Token count, retrieved schemas, and selected capability",
        mode: "Live terminal",
        path: "chapter4/active-tool-discovery/"
      }
    ],
    findings: [
      "Priority is a product policy, not merely a queue implementation detail.",
      "Graceful interruption requires tools and loops to expose safe cancellation points.",
      "On-demand discovery keeps a small stable prefix while preserving a large action space."
    ],
    boundary: "Today's models are trained mostly on synchronous trajectories; async behavior remains a Harness workaround.",
    rule: "Separate event intake, scheduling, model turns, tool execution, and user notification into explicit components.",
    extensions: [
      ["Parallel and state demos", "chapter4/async-agent/"],
      ["Active tool selection", "chapter4/active-tool-selection/"],
      ["Hierarchical matching", "book-en/images/fig4-7.svg"],
      ["Dynamic tool cache design", "book-en/images/fig4-8.svg"]
    ],
    reflection: "Which external event should interrupt current work rather than wait in a queue?",
    next: "Use code as the most general action interface."
  },
  {
    number: 18,
    chapter: "Chapter 5",
    part: "Coding Agents",
    title: "Why Is Code Generation Not Enough to Build a Coding Agent?",
    subtitle: "Files, execution, harness recovery, and bounded verification",
    book: "Coding as a Foundational Capability; Sessionless Design; Harness Engineering; Failure Recovery",
    figure: "fig5-2.svg",
    figureAlt: "Coding Agent workflow",
    question: "What turns a generated patch into a reliable change to a real repository?",
    stakes: [
      ["Workspace", "Files provide durable, inspectable state outside the context window."],
      ["Action", "Search, editing, and execution tools let the Agent change that state."],
      ["Evidence", "Compilers, tests, and renderers expose mistakes independently."]
    ],
    concepts: [
      ["Inspect", "Search before reading; locate the smallest relevant surface"],
      ["Modify", "Apply localized, reviewable edits"],
      ["Recover", "Classify evidence, revise one hypothesis, and stop safely"]
    ],
    contrast: {
      leftTitle: "Chat code generation",
      left: ["Produces a snippet", "Cannot observe repository state", "Leaves verification to the user"],
      rightTitle: "Coding Agent",
      right: ["Navigates a workspace", "Executes and revises", "Stops with evidence"],
      caption: "A workbench and recovery loop turn generation into engineering."
    },
    code: {
      title: "Verification drives the next action",
      lang: "python",
      lines: [
        "for attempt in range(max_attempts):",
        "    patch = edit(inspect(task, workspace))",
        "    evidence = verify(patch)",
        "    if evidence.passed: return commit(patch)",
        "    task = revise_hypothesis(evidence)",
        "return stop_safely(evidence)"
      ]
    },
    experiments: [
      {
        id: "Coding workflow",
        name: "Run a write-search-edit-verify workflow",
        duration: 2,
        command: "uv run pytest -q chapter5/coding-agent/tests/test_integration.py::TestToolChaining::test_write_search_edit_workflow",
        watch: "A real file moves through write, search, localized edit, and independent verification",
        mode: "Offline workflow",
        path: "chapter5/coding-agent/tests/"
      },
      {
        id: "Harness tests",
        name: "Run editing and shell-session contracts",
        duration: 1,
        command: "uv run pytest -q chapter5/coding-agent/tests/test_edit_tool.py chapter5/coding-agent/tests/test_shell_session.py",
        watch: "Exact-match edits, failure messages, state preservation, and safe boundaries",
        mode: "Live terminal",
        path: "chapter5/coding-agent/tests/"
      }
    ],
    findings: [
      "Files make Agent state durable, inspectable, and reproducible.",
      "Tool and test failures become observations that guide the next hypothesis.",
      "A reliable loop distinguishes verified success, safe incompletion, and unsafe failure."
    ],
    boundary: "Passing available tests proves only their covered properties; the same workbench also exposes credentials and destructive commands.",
    rule: "Treat coding as a bounded inspect–modify–verify loop, with an evidence-driven recovery path for every failure class.",
    extensions: [
      ["Coding Agent implementation", "chapter5/coding-agent/"],
      ["Complete Coding Agent test suite", "chapter5/coding-agent/tests/"],
      ["Search-tool comparison", "book-en/images/fig5-3.svg"],
      ["File-editing comparison", "book-en/images/fig5-4.svg"]
    ],
    reflection: "Which verifier would give your coding Agent genuinely new evidence after a wrong edit?",
    next: "Use code to improve reasoning and enforce strict business rules."
  },
  {
    number: 19,
    chapter: "Chapter 5",
    part: "Coding Agents",
    title: "When Should an Agent Think in Code Instead of Words?",
    subtitle: "Math, logic, and deterministic business constraints",
    book: "Code as a Thinking Tool; Code as a Constraint for Business Rules",
    figure: "fig5-10.svg",
    figureAlt: "Agent bootstrapping loop",
    question: "Which parts of a task should remain probabilistic, and which should become executable?",
    stakes: [
      ["Calculation", "Delegate exact arithmetic to a runtime."],
      ["Logic", "Translate constraints into a solver."],
      ["Policy", "Use server-side ground truth for irreversible decisions."]
    ],
    concepts: [
      ["Formalization", "Convert a verbal problem into variables and constraints"],
      ["Execution feedback", "The environment returns exact results or errors"],
      ["Three-tier rule safety", "Prompt → checklist → server gate"]
    ],
    contrast: {
      leftTitle: "Language-only",
      left: ["Flexible explanation", "Probabilistic arithmetic", "May invent policy facts"],
      rightTitle: "Code-assisted",
      right: ["Exact execution", "Testable constraints", "Independent ground truth"],
      caption: "Use language to interpret and code to guarantee."
    },
    code: {
      title: "Never trust self-reported policy facts",
      lang: "python",
      lines: [
        "order = db.get(order_id)",
        "now = server_clock.now()",
        "eligible = policy.check(order, now)",
        "if not eligible:",
        "    return reject_with_reason(order)"
      ]
    },
    experiments: [
      {
        id: "5-1",
        name: "Self-check code-assisted math",
        duration: 2,
        command: "uv run python chapter5/code-for-math/demo.py --selfcheck",
        watch: "Exact sandbox execution and scoring against truth",
        mode: "Live terminal",
        path: "chapter5/code-for-math/"
      },
      {
        id: "5-2",
        name: "Solve logic as constraints",
        duration: 2,
        command: "uv run python chapter5/code-for-logic/demo.py --mode solver --min-people 4",
        watch: "Variables, biconditional constraints, and verified solutions",
        mode: "Live terminal",
        path: "chapter5/code-for-logic/"
      },
      {
        id: "5-3",
        name: "Run codified-rule self-tests",
        duration: 2,
        command: "uv run python chapter5/small-model-codified-rules/demo.py --selftest",
        watch: "Checklist guidance versus server-side enforcement",
        mode: "Live terminal",
        path: "chapter5/small-model-codified-rules/"
      }
    ],
    findings: [
      "Code replaces fragile mental computation with exact environmental feedback.",
      "Constraint solvers reveal whether a verbal interpretation is internally consistent.",
      "Critical rules must obtain facts from sources the model cannot forge."
    ],
    boundary: "Formalization can encode the wrong problem perfectly; interpretation still needs review.",
    rule: "Use the model to translate intent, code to enforce invariants, and tests to verify the translation.",
    extensions: [
      ["Full math comparison", "chapter5/code-for-math/"],
      ["Full logic comparison", "chapter5/code-for-logic/"],
      ["Codified-rules campaign", "chapter5/small-model-codified-rules/"]
    ],
    reflection: "Which rule in your product is too important to exist only as natural language?",
    next: "Generate visual artifacts by writing code, rendering pixels, and reviewing the result."
  },
  {
    number: 20,
    chapter: "Chapter 5",
    part: "Coding Agents",
    title: "How Can an Agent Create Media It Can Actually Verify?",
    subtitle: "Slidev, rendering, multimodal review, and video editing",
    book: "Code-Driven Multimedia Generation; Proposer-Reviewer; Video Editing",
    figure: "fig5-5.svg",
    figureAlt: "Proposer-Reviewer loop for presentation generation",
    question: "How can an Agent know whether generated slide code is readable after it renders?",
    stakes: [
      ["Proposer", "Plans content and writes artifact code."],
      ["Renderer", "Converts code into the pixels users will see."],
      ["Reviewer", "Receives new visual evidence and returns structured fixes."]
    ],
    concepts: [
      ["Artifact loop", "Source → render → inspect → revise"],
      ["Context separation", "Proposer keeps text; Reviewer sees current pixels"],
      ["Explicit stop", "Quality gate or maximum iterations"]
    ],
    contrast: {
      leftTitle: "Self-review source",
      left: ["Sees intended layout", "Cannot observe overflow", "Repeats assumptions"],
      rightTitle: "Rendered review",
      right: ["Sees actual pixels", "Detects crowding and clipping", "Returns page-specific evidence"],
      caption: "The verifier is valuable because it receives new information."
    },
    code: {
      title: "Render before judging",
      lang: "python",
      lines: [
        "source = proposer.create_slidev(content)",
        "images = renderer.export_png(source)",
        "issues = vision_reviewer.inspect(images)",
        "while issues.blocking:",
        "    source = proposer.revise(source, issues)"
      ]
    },
    experiments: [
      {
        id: "5-4",
        name: "Run the offline Slidev review loop",
        duration: 3,
        command: "uv run python chapter5/paper-to-ppt/demo.py --dry-run",
        watch: "Crowded draft, rendered evidence, structured feedback, revised deck",
        mode: "Live terminal",
        path: "chapter5/paper-to-ppt/"
      },
      {
        id: "5-6",
        name: "Smoke-test code-driven video editing",
        duration: 2,
        command: "uv run python chapter5/video-edit/demo.py --smoke",
        watch: "Generated editing script, executable path, and keyframe validation",
        mode: "Live terminal",
        path: "chapter5/video-edit/"
      }
    ],
    findings: [
      "Source correctness and visual correctness are different properties.",
      "Separating generation and visual review controls multimodal context growth.",
      "Coarse-to-fine visual sampling reduces the cost of locating video events."
    ],
    boundary: "A visual reviewer can catch layout defects but may still miss factual or pedagogical errors.",
    rule: "Verify generated media in the modality consumed by the user.",
    extensions: [
      ["Experiment 5-5: narrated video pipeline", "chapter5/paper-to-video/"],
      ["Presentation rendering artifacts", "chapter5/paper-to-ppt/validation/"],
      ["Paper-to-video evidence", "chapter5/paper-to-video/validation/"],
      ["Video pipeline diagram", "book-en/images/fig5-6.svg"]
    ],
    reflection: "What new evidence becomes available only after your artifact is rendered or executed?",
    next: "Use generated code to connect systems, create interfaces, and bootstrap new Agents."
  },
  {
    number: 21,
    chapter: "Chapter 5",
    part: "Coding Agents",
    title: "How Can Code Let an Agent Create New Capabilities?",
    subtitle: "Adapters, generative UI, hot repair, and Agent bootstrapping",
    book: "Code as a System Adapter; Generative UI; Agent Bootstrapping",
    figure: "fig5-11.svg",
    figureAlt: "Pipeline of an Agent that creates Agents",
    question: "What changes when code becomes a tool for producing new tools and interfaces?",
    stakes: [
      ["Adapter", "Translate unstable external formats into stable internal ones."],
      ["Interface", "Generate a UI that matches the current intent."],
      ["Bootstrap", "Create a specialized Agent from a validated reference."]
    ],
    concepts: [
      ["Hot repair", "Failure sample → generated parser → tests → registration"],
      ["Artifact pattern", "Pass paths and queries instead of moving large data through tokens"],
      ["Validated generation", "Compile, test, scan, and exercise generated Agents"]
    ],
    contrast: {
      leftTitle: "One-off generation",
      left: ["Produces an artifact", "Capability disappears after task", "No reuse gate"],
      rightTitle: "Capability creation",
      right: ["Packages implementation", "Validates and versions it", "Reuses on later tasks"],
      caption: "Bootstrapping begins when output becomes part of the next Agent."
    },
    code: {
      title: "Capability promotion needs gates",
      lang: "python",
      lines: [
        "candidate = agent.generate_tool(failure_sample)",
        "compile(candidate)",
        "run_security_scan(candidate)",
        "run_regression_tests(candidate)",
        "registry.promote(candidate)"
      ]
    },
    experiments: [
      {
        id: "5-7",
        name: "Repair an unknown log format",
        duration: 2,
        command: "uv run python chapter5/adaptive-log-parser/demo.py --offline",
        watch: "Failure detection, generated parser, tests, and later reuse",
        mode: "Live terminal",
        path: "chapter5/adaptive-log-parser/"
      },
      {
        id: "5-9",
        name: "Generate a dynamic form",
        duration: 2,
        command: "uv run python chapter5/dynamic-form/demo.py --offline",
        watch: "Intent gaps converted into fields and cascading constraints",
        mode: "Live terminal",
        path: "chapter5/dynamic-form/"
      },
      {
        id: "5-12",
        name: "Inspect Agent-creation validation gates",
        duration: 2,
        command: "uv run python chapter5/agent-creator/demo.py --no-live --output chapter5/agent-creator/runs/course-smoke",
        watch: "Scratch versus template generation, compile, tests, and protocol audit",
        mode: "Live terminal",
        path: "chapter5/agent-creator/"
      }
    ],
    findings: [
      "Generated adapters let a system follow changing data formats.",
      "Generative UI moves structured clarification out of slow chat turns.",
      "Reference-based Agent creation preserves a proven loop while specializing tools."
    ],
    boundary: "Self-modification is unsafe when the Agent can alter the validator that approves its own changes.",
    rule: "Promote generated code into capability only after independent security, functional, and reuse checks.",
    extensions: [
      ["Experiment 5-8: log diagnosis", "chapter5/log-diagnosis/"],
      ["Experiment 5-10: ERP SQL Agent", "chapter5/erp-agent/"],
      ["Experiment 5-11: conversational UI", "chapter5/conversational-ui/"],
      ["Dynamic form architecture", "book-en/images/fig5-8.svg"],
      ["SQL artifact pattern", "book-en/images/fig5-9.svg"]
    ],
    reflection: "Which generated artifact is safe to reuse, and who decides that it has become a capability?",
    next: "Measure whether any of these architectural changes actually improve the Agent."
  },
  {
    number: 22,
    chapter: "Chapter 6",
    part: "Agent Evaluation",
    title: "How Do You Test an Agent Instead of Its Final Answer?",
    subtitle: "Environments, state, datasets, and executable verification",
    book: "Automated Evaluation Environment; Evaluation Task Datasets; Simulation Environments",
    figure: "fig6-2.svg",
    figureAlt: "Tool-calling and human-computer interaction evaluation environments",
    question: "What must an evaluation reproduce before its score means anything?",
    stakes: [
      ["Initial state", "Every run begins from the same controllable world."],
      ["Interaction", "The Agent receives realistic tools, errors, and user disclosures."],
      ["Verification", "Success is read from external state—not self-reported." ]
    ],
    concepts: [
      ["Dataset", "Initial state + goal + boundary cases + success criteria"],
      ["Environment", "State transitions, reset, tools, and termination"],
      ["Protocol", "Tool-only tasks or progressive user simulation"]
    ],
    contrast: {
      leftTitle: "Answer benchmark",
      left: ["One prompt", "One response", "String or judge score"],
      rightTitle: "Agent evaluation",
      right: ["Mutable state", "Multi-turn trajectory", "Executable outcome checks"],
      caption: "An Agent can say the right thing while changing the world incorrectly."
    },
    code: {
      title: "Reset, act, and inspect",
      lang: "python",
      lines: [
        "state = environment.reset(case.seed)",
        "trajectory = agent.run(case.goal, environment.tools)",
        "outcome = environment.snapshot()",
        "passed = verifier.check(outcome, trajectory)",
        "store(case, trajectory, outcome, passed)"
      ]
    },
    experiments: [
      {
        id: "Evaluation control",
        name: "Score a reporting Agent from external state",
        duration: 2,
        command: "cd chapter6/public-health-reporting-eval && python demo.py",
        watch: "Tool-call correctness, arithmetic, evidence citations, and unsupported-claim vetoes",
        mode: "Live terminal",
        path: "chapter6/public-health-reporting-eval/"
      }
    ],
    findings: [
      "A resettable environment turns a trajectory into a repeatable experiment.",
      "Progressive disclosure tests whether an Agent knows what to ask.",
      "Objective state checks are stronger than judging the final prose alone."
    ],
    boundary: "A simulator is useful only within its fidelity envelope; its omissions and biases become the Agent's test world.",
    rule: "Define the initial state, allowed transitions, and external success check before writing evaluation prompts.",
    extensions: [
      ["Experiments 6-1 and 6-2: tau2-bench", "chapter6/tau2-bench/"],
      ["Terminal-Bench reproduction", "chapter6/terminal-bench/"],
      ["SWE-bench reproduction", "chapter6/SWE-bench/"],
      ["GAIA reproduction", "chapter6/GAIA/"],
      ["OSWorld reproduction", "chapter6/OSWorld/"],
      ["AndroidWorld source and analysis", "chapter6/android-world/"],
      ["OpenVLA + RoboTwin2 design", "chapter6/openvla-robotwin2-eval/"]
    ],
    reflection: "Which production state would reveal success even if the Agent's final message were hidden?",
    next: "Turn observable outcomes into metrics that are consistent, diagnostic, and hard to game."
  },
  {
    number: 23,
    chapter: "Chapter 6",
    part: "Agent Evaluation",
    title: "How Do You Judge Quality Without Hiding Failure?",
    subtitle: "Rubrics, vetoes, LLM judges, pairwise comparison, and Elo",
    book: "Evaluation Metrics System; LLM-as-a-Judge; Pairwise Comparison and Model Ranking",
    figure: "fig6-4.svg",
    figureAlt: "LLM-as-a-Judge evaluation pipeline",
    question: "How can an automated judge produce a useful signal without turning one score into false certainty?",
    stakes: [
      ["Dimensions", "Separate correctness, completeness, efficiency, and safety."],
      ["Evidence", "Require a reason tied to the source trajectory."],
      ["Vetoes", "Block catastrophic errors that an average would conceal."]
    ],
    concepts: [
      ["Rubric", "Observable levels with boundary examples"],
      ["Calibration", "Agreement, position bias, and human spot checks"],
      ["Pairwise ranking", "Compare A/B first; reconstruct relative strength later"]
    ],
    contrast: {
      leftTitle: "Single score",
      left: ["Easy to chart", "Failure causes disappear", "Can reward fluent hallucination"],
      rightTitle: "Structured judgment",
      right: ["Dimension scores", "Cited evidence", "Independent safety veto"],
      caption: "Aggregation should happen after diagnosis—not before it."
    },
    code: {
      title: "Keep the veto outside the average",
      lang: "python",
      lines: [
        "grades = judge.score(trajectory, rubric)",
        "hallucinated = verifier.unsupported_claim(trajectory)",
        "if hallucinated: return 0.0",
        "return weighted_mean(grades)",
        "# retain every grade and its evidence"
      ]
    },
    experiments: [
      {
        id: "6-3",
        name: "Compare memory systems with an offline scored control",
        duration: 2,
        command: "cd chapter3/user-memory-evaluation && python main.py --mode compare --metric keyword-recall --category layer3",
        watch: "How direct recall diverges from cross-session synthesis",
        mode: "Live terminal",
        path: "chapter3/user-memory-evaluation/"
      },
      {
        id: "6-6",
        name: "Recover a leaderboard from simulated pairwise votes",
        duration: 2,
        command: "cd chapter6/elo-leaderboard && python cli.py pipeline --source simulate --num-battles 1000 --method bradley-terry --bootstrap 20",
        watch: "Latent ranking, uncertainty intervals, and sensitivity to comparison data",
        mode: "Live terminal",
        path: "chapter6/elo-leaderboard/"
      }
    ],
    findings: [
      "A useful Rubric turns vague quality into inspectable decisions.",
      "A hallucination veto prevents polished falsehoods from averaging into a pass.",
      "Pairwise judgments are often easier than absolute scores, but their ranking is still data-dependent."
    ],
    boundary: "An LLM judge shares model biases, can be position-sensitive, and must not be treated as ground truth without calibration.",
    rule: "Ask the judge for dimension-level evidence, calibrate it, and keep hard safety failures outside weighted averages.",
    extensions: [
      ["Experiment 6-4: end-to-end memory systems", "chapter6/user-memory-system-evaluation/"],
      ["Experiment 6-5: TTS quality evaluation", "chapter6/tts-quality-eval/"],
      ["Structured Rubric implementation", "chapter3/user-memory-evaluation/validate_rubric.py"],
      ["Elo full-data validation", "chapter6/elo-leaderboard/validation/"]
    ],
    reflection: "Which failure in your domain deserves a veto rather than a lower average score?",
    next: "Use evaluation to select a whole Agent system—not merely a model name."
  },
  {
    number: 24,
    chapter: "Chapter 6",
    part: "Agent Evaluation",
    title: "Which Agent Should You Ship?",
    subtitle: "Model behavior, latency, cost, and evaluation-driven selection",
    book: "Evaluation-Driven Model Selection; Model Behavior; Cost Analysis; Continuous Iteration",
    figure: "fig6-7.svg",
    figureAlt: "Loop from benchmark results to system improvements",
    question: "Why is the highest benchmark score not enough to choose a production Agent?",
    stakes: [
      ["Quality", "Success, boundary behavior, and variance across task slices"],
      ["Behavior", "When the model searches, edits, retries, or stops"],
      ["Economics", "Latency, cache use, tokens, availability, and total task cost"]
    ],
    concepts: [
      ["Fixed Harness", "Swap models to locate a model-side bottleneck"],
      ["Ablation", "Remove one Harness component to measure its contribution"],
      ["Pareto frontier", "Choose a non-dominated quality/cost/latency point"]
    ],
    contrast: {
      leftTitle: "Leaderboard choice",
      left: ["One public score", "Unknown Harness", "Average case"],
      rightTitle: "Deployment choice",
      right: ["Your task distribution", "Your complete Harness", "Cost and failure boundaries"],
      caption: "The unit of selection is model + context + tools + runtime."
    },
    code: {
      title: "Filter before ranking",
      lang: "python",
      lines: [
        "eligible = [r for r in runs if r.safety_pass]",
        "eligible = [r for r in eligible if r.p95_latency < sla]",
        "frontier = pareto(eligible, maximize='success', minimize='cost')",
        "winner = validate_on_holdout(frontier)",
        "ship_with_feature_flag(winner)"
      ]
    },
    experiments: [
      {
        id: "6-8",
        name: "Recompute a full Agent cost breakdown",
        duration: 2,
        command: "cd chapter6/agent-cost-analysis && python demo.py --offline --scenario all",
        watch: "Per-step cost, cache savings, compression savings, and non-additive interactions",
        mode: "Live terminal",
        path: "chapter6/agent-cost-analysis/"
      },
      {
        id: "6-7",
        name: "Validate a fixed-Harness action-threshold experiment",
        duration: 2,
        command: "python -m unittest discover -s chapter6/model-action-threshold/tests -v",
        watch: "Event-boundary accounting, first-edit timing, rework, and independent final tests",
        mode: "Live terminal",
        path: "chapter6/model-action-threshold/"
      }
    ],
    findings: [
      "Different models carry different default tool-use policies inside the same Harness.",
      "Cache-friendly context and compression change cost without changing the task.",
      "A model upgrade is a hypothesis that must clear your own gates."
    ],
    boundary: "A smoke run verifies integration, not steady-state availability, tail latency, or statistical superiority.",
    rule: "Select on a domain-specific Pareto frontier after safety and reliability gates—not on a global leaderboard rank.",
    extensions: [
      ["Experiment 6-9: provider/model benchmark", "chapter6/model-benchmark/"],
      ["Experiment 6-10: full memory component matrix", "chapter6/user-memory-system-evaluation/"],
      ["Action-threshold canonical campaign", "chapter6/model-action-threshold/results/"],
      ["Cost-analysis sample trace", "chapter6/agent-cost-analysis/sample_trace.json"]
    ],
    reflection: "What is the first non-quality gate that would eliminate a model from your production shortlist?",
    next: "Build evaluation infrastructure that can distinguish a real improvement from noise."
  },
  {
    number: 25,
    chapter: "Chapter 6",
    part: "Agent Evaluation",
    title: "Did the Agent Improve—or Did the Numbers Move?",
    subtitle: "Significance, observability, ablations, and production evaluation",
    book: "Statistical Significance; Agent Observability; Internal Evaluation Infrastructure; Simulation Fidelity",
    figure: "fig6-6.svg",
    figureAlt: "Observability technology stack for Agent systems",
    question: "What evidence is required before an evaluation delta becomes an engineering decision?",
    stakes: [
      ["Uncertainty", "Repeated samples expose variance and paired differences."],
      ["Observability", "Traces connect aggregate regressions to mechanisms."],
      ["Release control", "Feature flags, A/B tests, rollback, and privacy-aware analytics"]
    ],
    concepts: [
      ["Paired test", "Run old and new systems on the same cases"],
      ["Confidence interval", "Report a plausible range—not only a mean"],
      ["Two-layer flags", "Separate mechanism enablement from experiment assignment"]
    ],
    contrast: {
      leftTitle: "Scoreboard",
      left: ["One aggregate", "No trace linkage", "Manual reruns"],
      rightTitle: "Evaluation infrastructure",
      right: ["Slices + uncertainty", "Trajectory-level observability", "Repeatable release gates"],
      caption: "The purpose of a benchmark report is to generate testable hypotheses."
    },
    code: {
      title: "Pair cases before estimating the delta",
      lang: "python",
      lines: [
        "deltas = [new[c] - old[c] for c in shared_cases]",
        "estimate, interval = bootstrap_mean(deltas)",
        "if interval.low <= 0: hold_release()",
        "else: canary(new_system)",
        "monitor_slices_and_rollback()"
      ]
    },
    experiments: [
      {
        id: "6-3 evidence",
        name: "Rebuild and audit structured-judge evidence",
        duration: 2,
        command: "cd chapter6/user-memory-system-evaluation && python build_63_evidence.py",
        watch: "Case coverage, immutable source hashes, judge dimensions, and veto records",
        mode: "Live terminal",
        path: "chapter6/user-memory-system-evaluation/"
      }
    ],
    findings: [
      "Paired case-level analysis is more sensitive than comparing unrelated averages.",
      "Traces make a regression actionable by revealing the failing mechanism.",
      "Evaluation becomes production infrastructure when it controls release and rollback."
    ],
    boundary: "Statistical significance does not imply practical importance, dataset validity, or simulation fidelity.",
    rule: "Ship only deltas that are repeatable, practically meaningful, slice-safe, and traceable to a plausible mechanism.",
    extensions: [
      ["Experiment 6-11: AndroidWorld failure analysis", "chapter6/android-world/"],
      ["Experiment 6-12: OpenVLA + RoboTwin2", "chapter6/openvla-robotwin2-eval/"],
      ["Simulation fidelity spectrum", "book-en/images/fig6-8.svg"],
      ["Production evaluation chapter", "book-en/chapter6.md"]
    ],
    reflection: "What would make a statistically significant improvement too small or too risky to ship?",
    next: "Use the evaluation environment as the practice ground for changing model behavior."
  },
  {
    number: 26,
    chapter: "Chapter 7",
    part: "Model Post-Training",
    title: "Why Does Model Training Happen in Three Stages?",
    subtitle: "Pre-training, SFT, RL, and the agent-environment loop",
    book: "Pre-training, SFT, RL: A Three-Stage Panorama; Classic RL Agents; Pre-training Basics",
    figure: "fig7-7.svg",
    figureAlt: "Q-learning and LLM Agent architectures in a treasure hunt",
    question: "What distinct capability does each training stage add—and why does their order matter?",
    stakes: [
      ["Pre-training", "Acquire language, priors, knowledge, and basic reasoning."],
      ["SFT", "Learn the response and tool-use protocol from demonstrations."],
      ["RL", "Explore decisions and increase actions that earn reward."]
    ],
    concepts: [
      ["Policy", "A probability distribution over the next action"],
      ["Environment", "The world that returns a new state and reward"],
      ["Update", "Move probability toward behavior supported by the signal"]
    ],
    contrast: {
      leftTitle: "Classic RL",
      left: ["Small state/action space", "Learns mainly from trials", "Explicit value estimates"],
      rightTitle: "LLM Agent",
      right: ["Language observations/actions", "Strong pretrained priors", "Reasons in context before acting"],
      caption: "The loop is shared; the representation and prior knowledge are radically different."
    },
    code: {
      title: "The Q-learning update",
      lang: "python",
      lines: [
        "target = reward + gamma * max(Q[next_state])",
        "error = target - Q[state, action]",
        "Q[state, action] += alpha * error",
        "state = next_state",
        "# experience changes the next choice"
      ]
    },
    experiments: [
      {
        id: "7-1",
        name: "Watch Q-learning discover hidden game mechanics",
        duration: 2,
        command: "cd chapter1/learning-from-experience && python experiment.py --mode qlearning --rl-episodes 10000 --eval-episodes 100 --seed 42",
        watch: "Learning curve, exploration decay, and final greedy success",
        mode: "Live terminal",
        path: "chapter1/learning-from-experience/"
      }
    ],
    findings: [
      "Pre-training supplies priors that tabular RL must discover from scratch.",
      "SFT and pre-training both predict tokens; their data and loss masks differ.",
      "RL needs an environment capable of producing a meaningful signal."
    ],
    boundary: "The treasure hunt clarifies the loop, but its small state space does not represent the scale of language-model training.",
    rule: "Before choosing a training method, name the capability, the representation it should change, and the signal available to teach it.",
    extensions: [
      ["Experiment 7-2: Q-learning vs. LLM Agent", "chapter1/learning-from-experience/"],
      ["Q-learning grid world", "book-en/images/fig7-3.svg"],
      ["Classic vs. modern Agent", "book-en/images/fig7-5.svg"],
      ["Training paradigm evolution", "book-en/images/fig7-6.svg"]
    ],
    reflection: "Which capability in your Agent comes from weights, and which is reconstructed from context every run?",
    next: "Decide when demonstrations are enough and when exploration is worth the cost."
  },
  {
    number: 27,
    chapter: "Chapter 7",
    part: "Model Post-Training",
    title: "When Should You Teach with Examples—and When with Rewards?",
    subtitle: "SFT, loss masking, distribution shift, and the form-first rule",
    book: "SFT; When to Choose SFT and When to Choose RL; Single-Turn Reinforcement Learning",
    figure: "fig7-11.svg",
    figureAlt: "SFT followed by RL as a two-stage training pipeline",
    question: "Is the target capability a stable mapping to imitate or a strategy that must survive new situations?",
    stakes: [
      ["SFT", "Dense token-level supervision; stable and sample-efficient."],
      ["RL", "Sparse trajectory feedback; costly but allows exploration."],
      ["Shift", "Test whether the learned behavior survives changed rules and inputs."]
    ],
    concepts: [
      ["Loss masking", "Supervise the assistant response—not the user prompt"],
      ["Form first", "Stabilize parsable output before optimizing strategy"],
      ["Holdout shift", "Change values or environments while preserving the rule"]
    ],
    contrast: {
      leftTitle: "Use SFT",
      left: ["Known demonstrations", "Format/style/protocol", "Deployment matches training"],
      rightTitle: "Consider RL",
      right: ["Outcome can be verified", "Many valid strategies", "Generalization under shift matters"],
      caption: "SFT and RL are sequential tools—not rival ideologies."
    },
    code: {
      title: "SFT masks the prompt tokens",
      lang: "python",
      lines: [
        "tokens = prompt_ids + response_ids",
        "labels = [-100] * len(prompt_ids) + response_ids",
        "loss = cross_entropy(model(tokens), labels)",
        "loss.backward()",
        "# only the demonstrated response is supervised"
      ]
    },
    experiments: [
      {
        id: "7-4 evidence",
        name: "Audit retained VLM pre-training and SFT evidence",
        duration: 2,
        command: "python chapter7/MiniMind-pretrain/validation/validate_vlm_evidence.py",
        watch: "Hashed outputs, blind judgments, matched configurations, and negative results",
        mode: "Live terminal",
        path: "chapter7/MiniMind-pretrain/"
      },
      {
        id: "7-5 evidence",
        name: "Audit continued-pretraining trade-offs",
        duration: 2,
        command: "python chapter7/continued-pretraining/validation/validate_evidence.py",
        watch: "New-language gain, retained English ability, and persistent factual errors",
        mode: "Live terminal",
        path: "chapter7/continued-pretraining/"
      }
    ],
    findings: [
      "SFT efficiently learns explicit protocols represented in examples.",
      "RL is justified when a verifier can reward strategies beyond one reference answer.",
      "Training gains must be tested beside retention and distribution-shift failures."
    ],
    boundary: "The slogan 'SFT memorizes, RL generalizes' is a tendency under controlled conditions—not a guarantee for every model and task.",
    rule: "Use SFT until output is stable; add RL only when exploration and verified generalization justify its cost.",
    extensions: [
      ["Experiment 7-3: MiniMind language training", "chapter7/MiniMind-pretrain/"],
      ["Experiment 7-11: SFT vs. RL reproduction", "chapter7/SFTvsRL/"],
      ["Experiment 7-6: Sesame speech SFT", "chapter7/sesame/"],
      ["Experiment 7-6: Orpheus speech SFT", "chapter7/orpheus/"],
      ["Experiment 7-7: multilingual reasoning", "chapter7/MultilingualReasoning/"]
    ],
    reflection: "What deployment change would reveal that your fine-tuned model learned an example instead of a rule?",
    next: "Translate preferences and outcomes into optimization signals without losing the base policy."
  },
  {
    number: 28,
    chapter: "Chapter 7",
    part: "Model Post-Training",
    title: "How Do Preferences Become a Trainable Signal?",
    subtitle: "RLHF, reward models, KL constraints, PPO, GRPO, and DPO",
    book: "RLHF: From Human Preferences to Reward Models; Comparison of RL Algorithms",
    figure: "fig7-13.svg",
    figureAlt: "Group Relative Policy Optimization flow",
    question: "How can human comparisons change a policy without letting optimization destroy useful behavior?",
    stakes: [
      ["Preference data", "Humans compare outputs more reliably than they author perfect ones."],
      ["Reward model", "Generalizes pairwise labels into a scalar training signal."],
      ["Reference policy", "KL pressure limits drift away from known behavior."]
    ],
    concepts: [
      ["PPO", "Actor + critic + clipped policy update"],
      ["GRPO", "Normalize rewards within a sampled response group"],
      ["DPO", "Optimize chosen over rejected responses without a rollout loop"]
    ],
    contrast: {
      leftTitle: "Outcome optimization",
      left: ["Can discover new outputs", "Requires rollouts", "Reward hacking risk"],
      rightTitle: "Preference optimization",
      right: ["Uses chosen/rejected pairs", "Simpler pipeline", "Bounded by offline data"],
      caption: "The algorithm changes how the signal is used—not whether the signal is valid."
    },
    code: {
      title: "A relative advantage removes the critic",
      lang: "python",
      lines: [
        "rewards = verifier(samples)",
        "adv = (rewards - rewards.mean()) / (rewards.std() + 1e-6)",
        "ratio = policy.prob(samples) / old_policy.prob(samples)",
        "loss = clipped_policy_loss(ratio, adv)",
        "loss += beta * kl(policy, reference)"
      ]
    },
    experiments: [
      {
        id: "RL evaluation check",
        name: "Run answer-extraction tests for an RL-trained reasoner",
        duration: 2,
        command: "python -m pytest chapter7/Intuitor/tests -q",
        watch: "Whether the evaluator recognizes the trained model's answer format without inflating accuracy",
        mode: "Live terminal",
        path: "chapter7/Intuitor/"
      }
    ],
    findings: [
      "Preference labels can train either an explicit reward model or a direct objective.",
      "Relative rewards reduce value-model complexity but do not fix a bad verifier.",
      "KL is a steering constraint, not proof that useful capabilities are retained."
    ],
    boundary: "Offline preference methods cannot explore behaviors absent from their comparison data.",
    rule: "Choose the simplest optimizer that can use your signal, then spend most of the effort validating the signal and holdout behavior.",
    extensions: [
      ["Intuitor training companion", "chapter7/Intuitor/"],
      ["verl RL training framework", "chapter7/verl/"],
      ["Tinker cookbook", "chapter7/tinker-cookbook/"],
      ["Reward paradigm evolution", "book-en/images/fig7-reward-paradigms.svg"]
    ],
    reflection: "What shortcut could maximize your proposed reward while making the real product worse?",
    next: "Move attention from algorithm names to the data and environment that define the signal."
  },
  {
    number: 29,
    chapter: "Chapter 7",
    part: "Model Post-Training",
    title: "Why Do Data and Environments Matter More Than the Algorithm?",
    subtitle: "Practice grounds, task distributions, synthetic data, and fidelity",
    book: "Data and Environment: More Important Than Algorithms; Model-Simulated Environments",
    figure: "fig7-1.svg",
    figureAlt: "Reinforcement learning agent-environment interaction loop",
    question: "If PPO and GRPO are available off the shelf, where does the real training advantage come from?",
    stakes: [
      ["Coverage", "Tasks must span the situations that deployment will create."],
      ["Fidelity", "Errors and transitions must resemble the real environment."],
      ["Density", "Useful information should survive filtering and reach the learner."]
    ],
    concepts: [
      ["Task distribution", "Optimize which examples are generated and sampled"],
      ["Environment model", "Simulate transitions when the real world is unavailable"],
      ["Data verifier", "Reject corrupt, ungrounded, or unparseable trajectories"]
    ],
    contrast: {
      leftTitle: "Algorithm-first",
      left: ["Tune optimizer knobs", "Reuse weak tasks", "Trust training reward"],
      rightTitle: "Signal-first",
      right: ["Design task coverage", "Audit environment fidelity", "Measure held-out outcomes"],
      caption: "A better optimizer learns the wrong lesson faster when the world is wrong."
    },
    code: {
      title: "Filter before the trajectory becomes data",
      lang: "python",
      lines: [
        "trajectory = policy.rollout(task, environment)",
        "receipt = verifier.inspect(trajectory)",
        "if receipt.grounded and receipt.complete:",
        "    replay_buffer.add(trajectory, receipt)",
        "sample_balanced(replay_buffer, task_slices)"
      ]
    },
    experiments: [
      {
        id: "7-9 data",
        name: "Inspect verified teacher trajectories before SFT",
        duration: 2,
        command: "cd chapter7/cot-distillation && python analyze_data.py --sft data/sft_cot_distill_aime_kimi_k3.jsonl --raw data/raw_trajectories_aime_kimi_k3.jsonl",
        watch: "Sample count, trajectory length, reflective behavior, and verifier failures",
        mode: "Live terminal",
        path: "chapter7/cot-distillation/"
      }
    ],
    findings: [
      "Training data quality includes task coverage, provenance, and verifier correctness.",
      "A model-simulated environment can scale practice but transfers its own biases.",
      "Reward curves must be checked against independent deployment-shaped evaluations."
    ],
    boundary: "Synthetic diversity does not guarantee real diversity when every example comes from the same generator and assumptions.",
    rule: "Invest first in realistic transitions, difficult boundary cases, and independent verification; tune the optimizer afterward.",
    extensions: [
      ["Experiment 7-8: prompt distillation", "chapter8/prompt-distillation/"],
      ["Experiment 7-9: CoT distillation", "chapter7/cot-distillation/"],
      ["Experiment 7-10: adaptive reasoning length", "chapter7/AdaptThink/"],
      ["Autodata and simulated-environment discussion", "book-en/chapter7.md"]
    ],
    reflection: "Which behavior in your simulator is easiest for a policy to exploit but impossible in production?",
    next: "Assign credit when one final outcome depends on many earlier decisions."
  },
  {
    number: 30,
    chapter: "Chapter 7",
    part: "Model Post-Training",
    title: "How Do You Reward a Long Agent Trajectory?",
    subtitle: "Credit assignment, reward density, process signals, and path penalties",
    book: "From Single-Turn to Multi-Turn; Credit Assignment; Process vs. Outcome Reward; RLVP",
    figure: "fig7-15.svg",
    figureAlt: "Credit assignment across a multi-turn interaction",
    question: "When the final result fails, which earlier tool choice should the model change?",
    stakes: [
      ["Sparse outcome", "One final bit leaves most actions unexplained."],
      ["Process evidence", "Tool errors and rule violations identify local mistakes."],
      ["Partial credit", "Reachable progress can rescue information from all-fail groups."]
    ],
    concepts: [
      ["Outcome reward", "Score the completed task—not a convenient proxy"],
      ["Process reward", "Evaluate intermediate reasoning or actions"],
      ["RLVP", "Reward the outcome; penalize verified path violations"]
    ],
    contrast: {
      leftTitle: "Outcome only",
      left: ["Objective final target", "Simple verifier", "Very sparse credit"],
      rightTitle: "Outcome + path evidence",
      right: ["Retains final goal", "Uses observed violations", "Denser diagnosis"],
      caption: "Path signals should constrain the route without replacing the destination."
    },
    code: {
      title: "Separate success from path violations",
      lang: "python",
      lines: [
        "outcome = task_verifier(final_state)",
        "violations = rule_verifier(trajectory)",
        "progress = reachable_subgoals(trajectory)",
        "reward = outcome - penalty(violations)",
        "reward += partial_credit(progress, only_if_all_fail=True)"
      ]
    },
    experiments: [
      {
        id: "7-14 gates",
        name: "Run verifier regressions for trajectory data",
        duration: 2,
        command: "python -m pytest chapter7/cot-distillation/test_student_pipeline.py chapter7/cot-distillation/test_empty_problems.py -q",
        watch: "Malformed samples rejected before they can become supervision",
        mode: "Live terminal",
        path: "chapter7/cot-distillation/"
      }
    ],
    findings: [
      "Multi-turn tasks turn one outcome into a temporal attribution problem.",
      "Environment feedback contains information that scalar outcome rewards discard.",
      "A process metric becomes dangerous when it is easier to optimize than the real goal."
    ],
    boundary: "An LLM process judge can reward plausible-looking steps that did not causally produce the outcome.",
    rule: "Keep an objective outcome gate, add only externally verified path signals, and test explicitly for reward hacking.",
    extensions: [
      ["Experiment 7-14: RLVP reproduction guide", "chapter7/RLVP/"],
      ["Experiment 7-12: spatial reasoning", "chapter7/SpatialReasoning/"],
      ["Experiment 7-13: SimpleVLA-RL", "chapter7/SimpleVLA-RL/"],
      ["Reward density spectrum", "book-en/images/fig7-reward-density.svg"]
    ],
    reflection: "Which intermediate signal in your Agent is evidence of progress, and which is merely correlated with it?",
    next: "Apply these signals to the combinatorial problem of learning when and how to call tools."
  },
  {
    number: 31,
    chapter: "Chapter 7",
    part: "Model Post-Training",
    title: "How Can a Model Learn to Use Tools with Fewer Samples?",
    subtitle: "Tool-call RL, sandbox feedback, distillation, and practical boundaries",
    book: "RL for Learning Tool Calling; Sample Efficiency; On-Policy Distillation; Practical Tips",
    figure: "fig7-16.svg",
    figureAlt: "Tool-calling reinforcement learning reward loop",
    question: "How do we teach a model a policy over tools when most trajectories fail and every rollout is expensive?",
    stakes: [
      ["Combinatorics", "Tool, argument, order, and stopping choices multiply quickly."],
      ["Grounding", "Sandbox and environment feedback reveal what language alone cannot."],
      ["Dense teaching", "Distillation supplies token-level targets on the student's own paths."]
    ],
    concepts: [
      ["ReTool", "Interleave text, code calls, and sandbox observations"],
      ["On-policy distillation", "Teacher scores the student's current trajectories token by token"],
      ["Self-distillation", "Privileged context turns the same model into a teacher"]
    ],
    contrast: {
      leftTitle: "Scalar RL signal",
      left: ["One reward per trajectory", "Many samples wasted", "Can discover beyond teacher"],
      rightTitle: "Dense distillation",
      right: ["Signal at each token", "Higher sample efficiency", "Teacher or privileged context required"],
      caption: "Both methods need trajectories shaped like real Agent interaction."
    },
    code: {
      title: "Learn on the student's own trajectory",
      lang: "python",
      lines: [
        "trajectory = student.rollout(task, tools)",
        "teacher_logits = teacher.score(trajectory, privileged_info)",
        "student_logits = student.score(trajectory)",
        "loss = token_kl(student_logits, teacher_logits)",
        "update(student, loss)"
      ]
    },
    experiments: [
      {
        id: "7-9 preflight",
        name: "Check whether a CoT student-training run is actually ready",
        duration: 2,
        command: "cd chapter7/cot-distillation && python train_student.py --preflight --train-data data/sft_cot_distill_aime_kimi_k3.jsonl --preflight-output validation/course-preflight.json",
        watch: "Data hash, sample count, dependencies, trainer compatibility, and CUDA readiness",
        mode: "Live terminal",
        path: "chapter7/cot-distillation/"
      }
    ],
    findings: [
      "Tool learning needs the same observation/action protocol at training and deployment.",
      "Dense teacher distributions can succeed where sparse RL stalls.",
      "A preflight separates a configured recipe from a completed training claim."
    ],
    boundary: "Distillation cannot exceed information available to the teacher or privileged context, and GPU readiness is not training evidence.",
    rule: "Match rollout shape to deployment, preserve tool feedback, and choose the densest trustworthy signal available.",
    extensions: [
      ["Experiment 7-15: ReTool", "chapter7/retool/"],
      ["Experiment 7-16: AWorld training", "chapter7/AWorld-train/"],
      ["AWorld source checkout", "chapter7/AWorld/"],
      ["On-policy distillation discussion", "book-en/chapter7.md"],
      ["Tool ecosystem architecture", "book-en/images/fig7-18.svg"]
    ],
    reflection: "Could privileged information make your current model a useful teacher for itself?",
    next: "Move learning beyond model weights into knowledge, instructions, programs, and the updater itself."
  },
  {
    number: 32,
    chapter: "Chapter 8",
    part: "Continual Evolution",
    title: "How Do Failed Trajectories Become Learning Signals?",
    subtitle: "Outcome verification, process rules, Rubrics, and cross-trajectory experience",
    book: "Deriving Learning Signals from Operational Trajectories; Consolidating Experience into Knowledge",
    figure: "fig8-2.svg",
    figureAlt: "Three-layer trajectory verification from outcomes to an LLM Rubric",
    question: "What must happen between a production failure and a reusable lesson?",
    stakes: [
      ["Outcome", "Read what changed in the environment."],
      ["Process", "Locate rule violations and ineffective decisions."],
      ["Meaning", "Use a Rubric for dimensions that code cannot settle."]
    ],
    concepts: [
      ["Trajectory verifier", "Outcome checks + process rules + language Rubric"],
      ["Contrastive evidence", "Compare success, partial success, and failure"],
      ["Experience document", "Mechanism + conditions + evidence + exceptions"]
    ],
    contrast: {
      leftTitle: "Save the trajectory",
      left: ["High detail", "Hard to retrieve", "Incidental actions become noise"],
      rightTitle: "Consolidate experience",
      right: ["Cross-run pattern", "Explicit applicability", "Evidence and counterexamples"],
      caption: "A trajectory is evidence; it is not yet a lesson."
    },
    code: {
      title: "Diagnose before updating",
      lang: "python",
      lines: [
        "outcome = environment_verifier(trajectory)",
        "violations = process_verifier(trajectory)",
        "rubric = semantic_judge(trajectory, outcome)",
        "diagnosis = triangulate(outcome, violations, rubric)",
        "experience = consolidate(similar_diagnoses)"
      ]
    },
    experiments: [
      {
        id: "8-1",
        name: "Diagnose customer-service trajectories with three evidence layers",
        duration: 2,
        command: "cd chapter8/trajectory-verifier && python demo.py",
        watch: "False promises, privacy violations, over-refusal, and cited evidence",
        mode: "Live terminal",
        path: "chapter8/trajectory-verifier/"
      },
      {
        id: "8-2",
        name: "Consolidate several trajectories into experience documents",
        duration: 2,
        command: "cd chapter8/gaia-experience && python demo_documents.py",
        watch: "Transfer gain, retrieval cost, negative transfer, and applicability conditions",
        mode: "Live terminal",
        path: "chapter8/gaia-experience/"
      }
    ],
    findings: [
      "Environment outcomes constrain what a language judge may claim.",
      "Failures and partial successes reveal conditions hidden by successful runs.",
      "Cross-trajectory documents can transfer while using fewer tokens than raw history."
    ],
    boundary: "A pattern supported by past trajectories may become obsolete after an API, policy, or environment change.",
    rule: "Promote experience only with provenance, applicability conditions, counterevidence, and a revalidation trigger.",
    extensions: [
      ["Trajectory verifier tests", "chapter8/trajectory-verifier/test_verifier.py"],
      ["Experience-document implementation", "chapter8/gaia-experience/"],
      ["Knowledge-document architecture", "book-en/images/fig8-4.svg"]
    ],
    reflection: "Which detail in a successful trajectory was causal, and how would you distinguish it from coincidence?",
    next: "Choose the artifact that should change: knowledge, instructions, programs, or parameters."
  },
  {
    number: 33,
    chapter: "Chapter 8",
    part: "Continual Evolution",
    title: "Where Should an Agent Store What It Learns?",
    subtitle: "Knowledge, instructions, programs, parameters, and meta-updates",
    book: "Four Methods for Continual Agent Evolution; Updating the Update Method",
    figure: "fig1-1.svg",
    figureAlt: "Three levels of persistent Agent capability updates",
    question: "Which representation makes a new capability easiest to verify, retrieve, change, and retire?",
    stakes: [
      ["Knowledge", "Facts and experience remain traceable and editable."],
      ["Instructions", "General procedures guide the model at inference time."],
      ["Programs", "Deterministic workflows enforce repeatable behavior."]
    ],
    concepts: [
      ["Parameters", "Implicit perception, style, and broad policies"],
      ["Local patch", "Change the smallest artifact that explains the failure"],
      ["Meta-update", "Improve the updater or workflow that creates artifacts"]
    ],
    contrast: {
      leftTitle: "Prompt patch",
      left: ["Fast to deploy", "Easy to inspect", "Global rules accumulate"],
      rightTitle: "Program promotion",
      right: ["Deterministic execution", "Tests and versioning", "Narrower applicability"],
      caption: "The most powerful update is not always the safest or cheapest one."
    },
    code: {
      title: "Route a lesson to the smallest carrier",
      lang: "python",
      lines: [
        "if lesson.is_fact: update_knowledge(lesson)",
        "elif lesson.is_rule: patch_skill(lesson)",
        "elif lesson.is_deterministic: compile_workflow(lesson)",
        "else: propose_parameter_training(lesson)",
        "validate_transfer_and_retention()"
      ]
    },
    experiments: [
      {
        id: "8-4",
        name: "Compile browser experience into a replayable workflow",
        duration: 2,
        command: "cd chapter8/browser-use-rpa && python workflow_validation_demo.py",
        watch: "State predicates, reset-and-replay, and failure when the page state changes",
        mode: "Live terminal",
        path: "chapter8/browser-use-rpa/"
      },
      {
        id: "Tool evolution",
        name: "Create, validate, register, and reuse an offline tool",
        duration: 2,
        command: "cd chapter8/self-evolving-tools && python demo.py --offline",
        watch: "Search miss, candidate creation, rejection gate, registration, and later reuse",
        mode: "Live terminal",
        path: "chapter8/self-evolving-tools/"
      }
    ],
    findings: [
      "Knowledge is easiest to trace; programs are easiest to execute deterministically.",
      "Reusable tools convert one successful solution into a new action capability.",
      "Local, reversible changes make causal evaluation and rollback possible."
    ],
    boundary: "A compiled workflow is brittle when its state predicates fail to capture meaningful environmental change.",
    rule: "Choose the most explicit, local, reversible representation that can express the capability reliably.",
    extensions: [
      ["Experiment 8-3: prompt auto-optimization", "chapter8/prompt-auto-optimization/"],
      ["Experiment 7-8: prompt distillation", "chapter8/prompt-distillation/"],
      ["Real browser-use extension", "chapter8/browser-use-rpa/README.md"],
      ["Self-evolving tool library", "chapter8/self-evolving-tools/"]
    ],
    reflection: "Could the behavior you want be a testable program instead of another sentence in the system prompt?",
    next: "Govern the complete loop so an improvement cannot approve or conceal its own regression."
  },
  {
    number: 34,
    chapter: "Chapter 8",
    part: "Continual Evolution",
    title: "How Can a Self-Modifying Agent Change Without Drifting?",
    subtitle: "Candidate gates, transfer, retention, rollback, and sleep learning",
    book: "Continual-Evolution Closed Loop; Safety Boundaries; Sleep Learning",
    figure: "fig8-1.svg",
    figureAlt: "Overall loop of continual Agent evolution",
    question: "What prevents one mistaken lesson from becoming a permanent production capability?",
    stakes: [
      ["Isolation", "Online tasks append evidence; offline jobs propose changes."],
      ["Independent gates", "The updater cannot alter validators or thresholds."],
      ["Lifecycle", "Canary, monitor, roll back, consolidate, expire, and prune."]
    ],
    concepts: [
      ["Candidate area", "New artifacts cannot serve production traffic"],
      ["Transfer + retention", "Improve held-out tasks without forgetting old ones"],
      ["Sleep learning", "Batch consolidation outside the online execution path"]
    ],
    contrast: {
      leftTitle: "Online self-edit",
      left: ["Immediate", "Noise becomes persistent", "Attack can cross sessions"],
      rightTitle: "Governed evolution",
      right: ["Immutable evidence", "Offline candidate", "Independent release + rollback"],
      caption: "The trusted root must remain outside the system it approves."
    },
    code: {
      title: "The updater cannot be its own authority",
      lang: "python",
      lines: [
        "candidate = updater.propose(immutable_evidence)",
        "security_gate.check(candidate)",
        "gain = evaluator.transfer(candidate)",
        "retention = evaluator.retention(candidate)",
        "release.canary(candidate, gain, retention)"
      ]
    },
    experiments: [
      {
        id: "8-5",
        name: "Exercise self-modification safety regressions",
        duration: 2,
        command: "python -m pytest chapter8/self-modifying-agent/test_evolution.py -q",
        watch: "Rejected candidates, circuit breakers, regression gates, canary, and rollback",
        mode: "Live terminal",
        path: "chapter8/self-modifying-agent/"
      },
      {
        id: "8-6",
        name: "Compare static, append-only, and evolving Agents",
        duration: 2,
        command: "cd chapter8/self-evolution-eval && python demo.py --profile all --output output/course-reference.json",
        watch: "Learning, transfer, rule replacement, retention, and negative transfer",
        mode: "Live terminal",
        path: "chapter8/self-evolution-eval/"
      }
    ],
    findings: [
      "Appending feedback is not the same as replacing obsolete knowledge.",
      "Updater quality and the task Agent's ability to activate an artifact are separate capabilities.",
      "Long-term progress requires transfer, retention, safety, and maintenance metrics together."
    ],
    boundary: "A verifiable loop can optimize a proxy perfectly while making no progress on an ambiguous real objective.",
    rule: "Separate evidence, candidate, validator, and production authority—and preserve an immutable rollback path.",
    extensions: [
      ["Self-modifying Agent official runner", "chapter8/self-modifying-agent/run_experiment_8_5.py"],
      ["Longitudinal evaluation tests", "chapter8/self-evolution-eval/"],
      ["Overall continual-evolution loop", "book-en/images/fig8-1.svg"],
      ["Chapter 8 safety boundaries", "book-en/chapter8.md"]
    ],
    reflection: "Which file, threshold, or permission must your updater never be allowed to modify?",
    next: "Carry the perceive-think-act loop into voice, screens, and physical systems under real-time constraints."
  },
  {
    number: 35,
    chapter: "Chapter 9",
    part: "Multimodal Interaction",
    title: "Why Does a Voice Agent Feel Slow?",
    subtitle: "Cascaded pipelines, latency waterfalls, streaming, and turn detection",
    book: "Voice; Cascaded Pipeline; Full-Chain Streaming; Streaming Voice Perception",
    figure: "fig9-2.svg",
    figureAlt: "Latency waterfall for a serial voice pipeline",
    question: "Where does the silence between the user finishing and the Agent speaking actually come from?",
    stakes: [
      ["Turn detection", "VAD waits for silence and can cut off a thinking pause."],
      ["Serial work", "ASR, LLM, and TTS latency accumulate when stages wait."],
      ["Queueing", "High utilization amplifies latency nonlinearly."]
    ],
    concepts: [
      ["Cascaded", "VAD → ASR → LLM → TTS"],
      ["Streaming", "Emit partial transcripts, tokens, and audio chunks early"],
      ["Convergence", "Early recognition is fast but may change as context arrives"]
    ],
    contrast: {
      leftTitle: "Wait for completion",
      left: ["Stable transcript", "Simple control", "Every stage adds delay"],
      rightTitle: "Stream the chain",
      right: ["Earlier first audio", "Overlapped work", "Corrections and cancellation required"],
      caption: "Streaming changes when information becomes available—not the component boundaries."
    },
    code: {
      title: "Pipeline stages should overlap",
      lang: "python",
      lines: [
        "async for partial_text in asr.stream(audio):",
        "    llm.update(partial_text)",
        "async for sentence in llm.sentences():",
        "    tts.enqueue(sentence)",
        "if user_interrupts(): cancel_output()"
      ]
    },
    experiments: [
      {
        id: "9-1",
        name: "Preflight a cascaded voice Agent",
        duration: 1,
        command: "cd chapter9/live-audio/backend && npm run check",
        watch: "VAD model, ASR/LLM/TTS provider configuration, and missing runtime prerequisites",
        mode: "Live terminal",
        path: "chapter9/live-audio/"
      },
      {
        id: "9-2",
        name: "Generate controlled streaming-ASR scenarios",
        duration: 2,
        command: "cd chapter9/streaming-speech && python prepare_scenarios.py audio/sentence.wav validation/course-scenarios",
        watch: "Normal speech, a 900 ms pause, and background noise under identical source content",
        mode: "Live terminal",
        path: "chapter9/streaming-speech/"
      }
    ],
    findings: [
      "The silence threshold is both a latency control and a turn-taking assumption.",
      "Streaming hides work behind speech but introduces unstable partial hypotheses.",
      "Time to first useful audio matters more than full-response completion time."
    ],
    boundary: "A setup check or generated audio scenario verifies wiring and controls—not human conversational quality.",
    rule: "Instrument the latency of every boundary, then stream and overlap only where cancellation and correction are designed.",
    extensions: [
      ["Add-on (historical 9-2): browser WebRTC phone Agent", "chapter9/phone-agent/"],
      ["Streaming-speech official runner", "chapter9/streaming-speech/run_official_experiment.py"],
      ["Serial voice architecture", "book-en/images/fig9-1.svg"],
      ["Queueing latency", "book-en/images/fig9-3.svg"]
    ],
    reflection: "Which latency number would best predict whether a user interrupts or abandons your voice Agent?",
    next: "Remove more boundaries—and decide what fast interaction should do while slow reasoning continues."
  },
  {
    number: 36,
    chapter: "Chapter 9",
    part: "Multimodal Interaction",
    title: "When Should Voice Stop Taking Turns?",
    subtitle: "Omni, full-duplex interaction, fast-slow thinking, and controllable speech",
    book: "End-to-End Omnimodal Models; Full-Duplex Models; Thinking Architectures; Human-like Speech",
    figure: "fig9-5.svg",
    figureAlt: "Fast and slow thinking architecture alternatives",
    question: "How can an Agent listen, speak, interrupt, and think deeply without making conversation stall?",
    stakes: [
      ["Omni", "Preserve prosody and emotion across one end-to-end model."],
      ["Full duplex", "Choose listen/speak/stop actions many times per second."],
      ["Fast + slow", "Keep interaction alive while a strategist works in the background."]
    ],
    concepts: [
      ["Turn-based Omni", "End-to-end audio but still waits for a turn boundary"],
      ["Interactive model", "Concurrent input/output with barge-in and backchannels"],
      ["Latent bridge", "Exchange richer internal state than plain text"]
    ],
    contrast: {
      leftTitle: "Modular cascade",
      left: ["Easy to debug", "Providers interchangeable", "Prosody lost through text"],
      rightTitle: "End-to-end/full duplex",
      right: ["Lower boundary latency", "Preserves acoustic cues", "Harder to observe and control"],
      caption: "The newer architecture buys interaction quality with reduced modularity."
    },
    code: {
      title: "Fast interaction can delegate",
      lang: "python",
      lines: [
        "intent = realtime_model.listen(audio_frame)",
        "if intent.needs_deep_work:",
        "    job = strategist.start(intent.context)",
        "realtime_model.respond(interaction_state)",
        "if job.ready: realtime_model.integrate(job.result)"
      ]
    },
    experiments: [
      {
        id: "9-3",
        name: "Test the end-to-end speech contract offline",
        duration: 2,
        command: "python -m pytest chapter9/end-to-end-speech/test_step_audio.py chapter9/end-to-end-speech/test_none_content.py -q",
        watch: "Exact model contract, audio response handling, and fail-closed behavior without an endpoint",
        mode: "Live terminal",
        path: "chapter9/end-to-end-speech/"
      },
      {
        id: "9-4",
        name: "Audit controllable-speech media and listening evidence",
        duration: 2,
        command: "cd chapter9/controllable-tts && python validate_artifacts.py",
        watch: "24 reference profiles, routed controls, media hashes, and the distinction from human MOS",
        mode: "Live terminal",
        path: "chapter9/controllable-tts/"
      }
    ],
    findings: [
      "Full-duplex models replace discrete turns with continuous interaction decisions.",
      "Fast-slow separation preserves responsiveness without forcing every answer to be shallow.",
      "Voice quality must be judged from audio—not configuration labels or text transcripts."
    ],
    boundary: "End-to-end behavior is harder to attribute to ASR, reasoning, timing, or synthesis when a failure occurs.",
    rule: "Choose the simplest voice architecture that meets the interaction target, and preserve modality-native observability at every boundary you remove.",
    extensions: [
      ["Step-Audio R1 upstream audit", "chapter9/end-to-end-speech/validation/upstream_audit.json"],
      ["Controllable TTS listening study", "chapter9/controllable-tts/validation/audio_quality_study.json"],
      ["Omni architecture comparison", "book-en/images/fig9-4.svg"],
      ["Step-Audio dual-brain architecture", "book-en/images/fig9-6.svg"]
    ],
    reflection: "What should your fast interaction model be allowed to say before the slow model has verified the answer?",
    next: "Carry perception and action into visual interfaces, where every click changes the next observation."
  },
  {
    number: 37,
    chapter: "Chapter 9",
    part: "Multimodal Interaction",
    title: "How Does an Agent Act Through Pixels?",
    subtitle: "GUI action spaces, visual grounding, and bounded interaction",
    book: "Computer Use; Action Space Design; Visual Grounding; Real-Time Performance",
    figure: "fig9-9.svg",
    figureAlt: "Visual grounding with annotated interface elements",
    question: "How does an Agent turn a screenshot and a goal into the right interface action?",
    stakes: [
      ["Observation", "A screenshot is a partial, time-sensitive view of application state."],
      ["Grounding", "The Agent must map language to an element ID or coordinate."],
      ["Interaction", "Every click or keystroke changes the next observation."]
    ],
    concepts: [
      ["Structured tree", "Use DOM or accessibility elements when they are reliable"],
      ["Visual grounding", "Locate targets directly in pixels when structure is absent"],
      ["Bounded loop", "Observe → one guarded action → observe again"]
    ],
    contrast: {
      leftTitle: "Structured grounding",
      left: ["DOM/accessibility IDs", "Closed-set selection", "Fails on custom drawing"],
      rightTitle: "Visual grounding",
      right: ["Works from pixels", "General interface coverage", "Coordinate and scale errors"],
      caption: "Production systems need both paths, coordinate transforms, and a confidence-aware fallback."
    },
    code: {
      title: "Every action creates a new observation",
      lang: "python",
      lines: [
        "while budget.remaining:",
        "    screenshot, tree = browser.observe()",
        "    target = agent.ground(task, screenshot, tree)",
        "    action = agent.choose_action(target)",
        "    receipt = browser.execute(guard(action))",
        "    if verifier.done(receipt): break"
      ]
    },
    experiments: [
      {
        id: "9-6 preflight",
        name: "Run offline Computer Use contract checks",
        duration: 2,
        command: "python -m pytest chapter9/computer-use-open-model/tests -q",
        watch: "Endpoint identity, screenshot retention, manifest integrity, and redaction boundaries",
        mode: "Offline preflight",
        path: "chapter9/computer-use-open-model/"
      },
      {
        id: "9-6 retained status",
        name: "Inspect the retained open-model acceptance pointer",
        duration: 1,
        command: "python -m json.tool chapter9/computer-use-open-model/validation/latest.json",
        watch: "Experiment arm, model scope, status, and the hashes required to trace the full run",
        mode: "Retained evidence",
        path: "chapter9/computer-use-open-model/validation/"
      }
    ],
    findings: [
      "A Computer Use result is a trajectory of state changes—not a final textual answer.",
      "Structured elements improve precision, while pixel grounding expands interface coverage.",
      "Scaling, coordinate transforms, stale screenshots, and hidden state create distinct failure modes."
    ],
    boundary: "Offline contract tests and an acceptance pointer do not reproduce the retained browser trajectory or complete the separate Anthropic-native arm.",
    rule: "Execute one bounded GUI action at a time, re-observe after every state change, and retain screenshots plus external outcome evidence.",
    extensions: [
      ["Experiment 9-5: Claude Computer Use", "chapter9/claude-quickstarts/computer-use-demo/"],
      ["Experiment 9-6: open-model Computer Use", "chapter9/computer-use-open-model/"],
      ["Screenshot-action loop", "book-en/images/fig9-7.svg"],
      ["Coordinate scaling", "book-en/images/fig9-10.svg"]
    ],
    reflection: "Which state change would prove that your GUI action succeeded, even if the Agent claims it did?",
    next: "Cross from visual interfaces into physical control, where latency and mistakes have mechanical consequences."
  },
  {
    number: 38,
    chapter: "Chapter 9",
    part: "Multimodal Interaction",
    title: "How Does an Agent Turn Plans into Physical Actions?",
    subtitle: "Planning-control separation, VLA control, safety gates, and Sim2Real",
    book: "Robot Manipulation; Planning and Control; VLA Control; Sim2Real Transfer",
    figure: "fig9-11.svg",
    figureAlt: "Vision-Language-Action model architecture",
    question: "How can slow semantic planning drive fast physical control without losing safety?",
    stakes: [
      ["Planning", "A vision-language model selects goals and interprets the scene."],
      ["Control", "A fast policy turns the current observation into motor commands."],
      ["Safety", "External gates must constrain forces, motion, workspace, and authority."]
    ],
    concepts: [
      ["Two-layer loop", "Slow planning chooses subgoals; fast control executes motion"],
      ["Action chunking", "Predict several future controls per expensive inference"],
      ["Sim2Real", "Train across calibrated visual and physical variation"]
    ],
    contrast: {
      leftTitle: "Open-loop plan",
      left: ["Commit to a long motion", "Assume the world stays fixed", "Detect errors late"],
      rightTitle: "Guarded feedback loop",
      right: ["Short action horizon", "Re-observe continuously", "Interrupt on state change"],
      caption: "Physical autonomy depends on feedback frequency and authority boundaries."
    },
    code: {
      title: "Slow plan, fast guarded control",
      lang: "python",
      lines: [
        "subgoal = planner.choose(observation, task)",
        "chunk = controller.predict(observation, subgoal)",
        "for action in safety_filter(chunk):",
        "    robot.execute(action)",
        "    observation = robot.observe()",
        "    if world_changed(observation): break"
      ]
    },
    experiments: [
      {
        id: "9-9 dry configuration",
        name: "Inspect a fail-closed robot navigation contract",
        duration: 1,
        command: "python chapter9/gemini-xlerobot-navigation/navigation.py",
        watch: "Exact model ID, task, camera, three motion tools, decision frequency, and no actuation",
        mode: "Dry configuration",
        path: "chapter9/gemini-xlerobot-navigation/"
      },
      {
        id: "Robot safety gates",
        name: "Run evidence-validator regressions for physical experiments",
        duration: 2,
        command: "python chapter9/xlerobot-teleoperation/test_validator.py && python chapter9/gemini-xlerobot-navigation/test_validator.py && python chapter9/rgb-sim2real-grasping/test_validator.py",
        watch: "Why dry runs, mock artifacts, and unverified motion cannot satisfy completion",
        mode: "Offline validation",
        path: "chapter9/"
      }
    ],
    findings: [
      "Planning and control operate at different semantic and temporal scales.",
      "Action chunks reduce inference pressure but delay response to unexpected change.",
      "Physical completion requires calibrated hardware, authorization, measurements, and direct artifacts."
    ],
    boundary: "A source audit, preflight, validator test, or dry configuration demonstrates architecture and blockers—not a successful robot run.",
    rule: "Keep physical actions behind external safety gates, short feedback horizons, and measurements the model cannot fabricate.",
    extensions: [
      ["Experiment 9-7: XLeRobot teleoperation", "chapter9/xlerobot-teleoperation/"],
      ["Experiment 9-9: robot navigation", "chapter9/gemini-xlerobot-navigation/"],
      ["Experiment 9-11: RGB Sim2Real grasping", "chapter9/rgb-sim2real-grasping/"],
      ["Sim2Real pipeline", "book-en/images/fig9-13.svg"]
    ],
    reflection: "How quickly must a physical controller reconsider an action when the world changes unexpectedly?",
    next: "Scale from one Agent loop to several loops that exchange context, artifacts, and control."
  },
  {
    number: 39,
    chapter: "Chapter 10",
    part: "Multi-Agent Collaboration",
    title: "When Should Agents Share the Same Context?",
    subtitle: "Shared trajectories, isolated contexts, role switching, and handoffs",
    book: "Classification Framework; Shared vs. Non-Shared Context; Multi-Stage Role Switching",
    figure: "fig10-1.svg",
    figureAlt: "Shared-context and non-shared-context multi-Agent architectures",
    question: "Should the next specialist inherit everything—or receive only an explicit handoff package?",
    stakes: [
      ["Continuity", "Shared history preserves details and user decisions."],
      ["Isolation", "Separate contexts reduce interference and permission leakage."],
      ["Scale", "Independent contexts enable parallel work beyond one window."]
    ],
    concepts: [
      ["Shared context", "New prompt/tools, same complete trajectory"],
      ["Non-shared context", "Independent trajectory + explicit communication"],
      ["IPC analogy", "Files as shared memory; calls/messages as message passing"]
    ],
    contrast: {
      leftTitle: "Shared context",
      left: ["Near-zero handoff loss", "Mostly serial roles", "History grows and biases"],
      rightTitle: "Non-shared context",
      right: ["Modular and parallel", "Selective disclosure", "Handoff can omit evidence"],
      caption: "Share when loss is unacceptable; isolate when scale, focus, or security dominates."
    },
    code: {
      title: "A role is prompt + tools + visible state",
      lang: "python",
      lines: [
        "stage = router.choose(task_state)",
        "agent = Agent(prompt=stage.prompt, tools=stage.tools)",
        "if stage.shared:",
        "    agent.resume(full_trajectory)",
        "else: agent.start(handoff_package)"
      ]
    },
    experiments: [
      {
        id: "10-1",
        name: "Inspect staged prompts, tools, and fallback gates",
        duration: 1,
        command: "cd chapter10/staged-system-prompt && python demo.py --list-stages",
        watch: "Requirements, implementation, review, and revision boundaries",
        mode: "Live terminal",
        path: "chapter10/staged-system-prompt/"
      },
      {
        id: "10-2",
        name: "Inspect role-specific handoff capabilities",
        duration: 1,
        command: "cd chapter10/multi-role-transfer && python demo.py --list-roles",
        watch: "Distinct prompts, tools, transfer edges, and shared session state",
        mode: "Live terminal",
        path: "chapter10/multi-role-transfer/"
      }
    ],
    findings: [
      "Changing prompt and tools can create a specialist while preserving one trajectory.",
      "Shared context removes handoff compression but can carry framing bias across roles.",
      "Independent Agents require an explicit data plane and control plane."
    ],
    boundary: "Calling predefined stages 'multi-Agent' is useful architecturally, but the execution remains a workflow with a known path.",
    rule: "Choose context sharing before topology: it determines information loss, isolation, parallelism, and token growth.",
    extensions: [
      ["Stage-based role switching", "book-en/images/fig10-stage-switching.svg"],
      ["Staged-system full demo", "chapter10/staged-system-prompt/README.md"],
      ["Cross-domain transfer demo", "chapter10/multi-role-transfer/README.md"]
    ],
    reflection: "Which detail would be too dangerous to omit from a handoff—and which detail should not cross the boundary?",
    next: "Choose who coordinates independent Agents and how artifacts and messages move between them."
  },
  {
    number: 40,
    chapter: "Chapter 10",
    part: "Multi-Agent Collaboration",
    title: "Who Should Coordinate Independent Agents?",
    subtitle: "Peer review, managers, decentralized handoffs, files, and control planes",
    book: "Non-Shared Context; File System; Communication and Control; Collaboration Topologies; A2A",
    figure: "fig10-4.svg",
    figureAlt: "Manager architecture for sequential multi-Agent coordination",
    question: "When Agents work in separate contexts, what structure keeps their work coherent?",
    stakes: [
      ["Peer loop", "A proposer and reviewer iterate with independent evidence."],
      ["Manager", "One planner decomposes, budgets, schedules, and integrates."],
      ["Decentralized", "Peers transfer work without a runtime central controller."]
    ],
    concepts: [
      ["Data plane", "Workspaces, shared artifacts, external and system mounts"],
      ["Control plane", "Spawn, message, status, terminate, and resource scheduling"],
      ["Handoff package", "Goal + evidence + artifacts + open questions + acceptance"]
    ],
    contrast: {
      leftTitle: "Manager topology",
      left: ["Global plan", "Simple supervision", "Planner is bottleneck"],
      rightTitle: "Decentralized topology",
      right: ["Local ownership", "Flexible handoffs", "Harder global consistency"],
      caption: "Topology determines where planning errors and coordination costs accumulate."
    },
    code: {
      title: "Pass artifacts; observe lifecycle",
      lang: "python",
      lines: [
        "job = manager.spawn(role, goal, budget)",
        "manager.message(job, evidence_paths)",
        "while job.running: manager.observe(job.status)",
        "result = manager.verify(job.artifacts)",
        "manager.cancel_dependents_if_satisfied(result)"
      ]
    },
    experiments: [
      {
        id: "10-3",
        name: "Rehearse a four-role translation orchestration",
        duration: 2,
        command: "cd chapter10/book-translation && python demo.py --dry-run",
        watch: "Manager plan, glossary ownership, chapter budgets, proofreading, and integration",
        mode: "Live terminal",
        path: "chapter10/book-translation/"
      }
    ],
    findings: [
      "Files handle large persistent artifacts; messages handle asynchronous coordination.",
      "The manager's decomposition quality caps the value of stronger workers.",
      "Explicit status and termination semantics matter as much as task prompts."
    ],
    boundary: "A dry-run proves the orchestration graph and budgets—not translation quality or multi-Agent advantage.",
    rule: "Make ownership, artifact contracts, lifecycle states, budgets, and termination paths explicit before adding Agents.",
    extensions: [
      ["Experiment 10-3: fixed baseline + autonomous phone registration", "chapter10/autonomous-phone-registration/"],
      ["Agent virtual file system", "book-en/images/fig10-2.svg"],
      ["Manager parallel coordination", "book-en/images/fig10-6.svg"],
      ["A2A and decentralized handoffs", "book-en/chapter10.md"]
    ],
    reflection: "If the manager decomposes the task incorrectly, which independent gate can detect the mistake before workers waste their budgets?",
    next: "Test whether multiple Agents create new information or merely spend more tokens."
  },
  {
    number: 41,
    chapter: "Chapter 10",
    part: "Multi-Agent Collaboration",
    title: "When Is Multi-Agent Actually Better Than One Agent?",
    subtitle: "Information gain, parallelism, verification, budgets, and cost",
    book: "When Is Multi-Agent Truly Better; Parallel Coordination; Budget Awareness",
    figure: "fig10-8.svg",
    figureAlt: "Parallel web research architecture",
    question: "What does collaboration add that a single Agent with the same compute could not obtain?",
    stakes: [
      ["New evidence", "Execution, rendering, browsing, and independent observations change the answer."],
      ["Parallel time", "Independent searches reduce wall-clock latency when resources allow."],
      ["Cost", "Multi-Agent systems may spend several times—or an order of magnitude—more tokens."]
    ],
    concepts: [
      ["Information gain", "The verifier observes something unavailable at generation time"],
      ["Single settlement", "One success can resolve the task and stop siblings"],
      ["Budget awareness", "Strategy changes with remaining steps and task value"]
    ],
    contrast: {
      leftTitle: "More voices",
      left: ["Same text", "Same evidence", "More samples and debate"],
      rightTitle: "More observations",
      right: ["Independent tools", "Execution or visual feedback", "Parallel environment interaction"],
      caption: "The advantage comes from information—not the number of Agent labels."
    },
    code: {
      title: "Settle once; cancel the rest",
      lang: "python",
      lines: [
        "jobs = spawn_parallel(search_shards)",
        "for result in as_completed(jobs):",
        "    evidence.merge(result.receipts)",
        "    if verifier.sufficient(evidence):",
        "        cancel_all(jobs); break"
      ]
    },
    experiments: [
      {
        id: "10-6",
        name: "Run parallel web research with independent browsers",
        duration: 3,
        command: "cd chapter10/parallel-web-research && python demo.py",
        watch: "Cited evidence, browser isolation, parallel speedup, timeout handling, and cleanup",
        mode: "Live terminal",
        path: "chapter10/parallel-web-research/"
      }
    ],
    findings: [
      "Debate over identical evidence often matches a single Agent at equal compute.",
      "External feedback can nearly double performance because it adds observations.",
      "Parallel speedup is real only when setup, contention, and cancellation costs are included."
    ],
    boundary: "A speedup on one site and network condition does not prove lower total cost or better answer quality for every research task.",
    rule: "Add an Agent only when it owns a distinct observation, permission boundary, artifact, or parallelizable environment interaction.",
    extensions: [
      ["Parallel research acceptance evidence", "chapter10/parallel-web-research/validation/"],
      ["Proposer-reviewer loop", "book-en/images/fig10-3.svg"],
      ["Phone + computer dual-Agent architecture", "book-en/images/fig10-7.svg"],
      ["Book translation Agent comparison", "chapter10/book-translation/"]
    ],
    reflection: "What new information does your proposed second Agent obtain that the first Agent cannot?",
    next: "Engineer against coordination failures—and examine what appears when Agent populations become societies."
  },
  {
    number: 42,
    chapter: "Chapter 10",
    part: "Multi-Agent Collaboration",
    title: "How Do Agent Teams Fail—and What Should We Build Next?",
    subtitle: "Conflicts, error cascades, Agent societies, and the course synthesis",
    book: "Failure Modes; Agent Society; Economic Competition; Strategic Gameplay",
    figure: "fig10-11.svg",
    figureAlt: "Voice Werewolf multi-Agent system",
    question: "How do we prevent local mistakes from becoming group failures while still allowing collective behavior to emerge?",
    stakes: [
      ["Concurrency", "Shared files can lose updates or encode semantic conflicts."],
      ["Cascades", "A wrong upstream claim is amplified by trusting downstream Agents."],
      ["Emergence", "Persistent Agents produce social, strategic, and economic behavior not explicitly scripted."]
    ],
    concepts: [
      ["Optimistic locking", "Detect version change before committing a shared write"],
      ["Information control", "A code judge reveals only what each role may know"],
      ["External reward", "Society outcomes are scored by the environment—not self-report"]
    ],
    contrast: {
      leftTitle: "Agent chat room",
      left: ["Everyone sees everything", "Loose role prompts", "Claims spread unchecked"],
      rightTitle: "Governed society",
      right: ["State authority in code", "Role-scoped views", "Auditable actions and rewards"],
      caption: "Social complexity requires stronger state and information governance."
    },
    code: {
      title: "The judge owns truth and disclosure",
      lang: "python",
      lines: [
        "private_view = judge.view_for(player, global_state)",
        "action = player.act(private_view)",
        "judge.validate(action, role=player.role)",
        "global_state = judge.apply(action)",
        "audit.append(player.id, action, state_hash(global_state))"
      ]
    },
    experiments: [
      {
        id: "10-8 offline diagnostic",
        name: "Run a deterministic information-isolation game",
        duration: 2,
        command: "cd chapter10/voice-werewolf && python demo.py --offline",
        watch: "Private role context, phase transitions, legal actions, votes, and winner gates",
        mode: "Live terminal",
        path: "chapter10/voice-werewolf/"
      }
    ],
    findings: [
      "Coordination failures are distributed-systems failures plus probabilistic decision errors.",
      "A code-driven authority can preserve information asymmetry and rule integrity.",
      "Social and economic simulations can generate new experience—but also collusion and pathology."
    ],
    boundary: "An offline all-AI diagnostic does not satisfy the book's live human voice acceptance criteria.",
    rule: "Keep shared truth, permissions, conflict detection, and final rewards outside the Agents that compete or collaborate.",
    extensions: [
      ["Experiment 10-5: Stanford Generative Agents", "https://github.com/joonspk-research/generative_agents"],
      ["Experiment 10-6: consent-gated voice path", "chapter10/voice-werewolf/README.md"],
      ["AI Town architecture", "book-en/images/fig10-10.svg"],
      ["Agent society and economy cases", "book-en/chapter10.md"]
    ],
    synthesis: [
      ["Build · Lessons 01–21", "Context → memory → tools → code"],
      ["Improve · Lessons 22–34", "Evaluation → training → continual evolution"],
      ["Expand · Lessons 35–42", "Voice → embodied action → collaboration"]
    ],
    reflection: "Which group-level failure cannot be prevented by improving any single Agent in isolation?",
    next: "Return to the course loop: define the failure, run a controlled experiment, interpret the evidence, and update safely."
  }
];
