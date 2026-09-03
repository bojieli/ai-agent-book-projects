# Evaluating Agents

The first six chapters laid out how to build a single Agent: its context, knowledge, tools, coding capabilities, and observation and action spaces. But completing a build does not mean the build is correct; only stable measurement can give subsequent model training and system evolution a reliable direction.

When building an Agent system, developers face numerous design choices that often lack obvious correct answers:

- Which model should be used?
- What tools should the model be able to call?
- What data should the knowledge base store, and how should it be structured?
- How should user memory be implemented?
- How should the model's prompts and Skills be organized?
- What constraints need to be added to the Harness?
- How should evaluation results be transformed into learning signals for the Agent's continuous evolution?

Evaluation puts these decisions on a scientific footing. Through systematic comparative experiments (change one variable at a time and observe the effect) and ablation experiments (disable one component at a time and observe how overall performance changes), you can distinguish genuine capability gains from superficial fluctuations—and avoid being penny wise and pound foolish. Software engineering has a saying: you can't improve what you don't measure. Without a repeatable evaluation system, an Agent can only be iterated on intuition.

From the perspective of Harness engineering introduced in Chapter 1, evaluation plays the core role of "verification" within the Harness. A key insight is: **the object of evaluation should not be just the model, but the combination of the model and the Harness**. The same model can perform wildly differently in different Harnesses — some teams have significantly improved the same model's performance on terminal tasks purely by optimizing the Harness (see Chapter 5). So when an Agent evaluates poorly, the fix may not be a different model but a better Harness component (prompts, tool design, feedback loops). A sound evaluation system should be able to tell apart two fundamentally different problems: "insufficient model capability" and "Harness design flaws." **A common way to tell them apart is the model swap experiment**: fix the Harness, swap in a stronger or weaker model, and watch how much the score moves. If a stronger model doesn't raise the score, the bottleneck is the Harness. If a weaker model tanks the score and results swing sharply with model capability, the most direct reading is that the model itself is the bottleneck and current performance is dominated by the model. Whether this is because the task is inherently hard or because the Harness relies too heavily on the model's prior knowledge requires further analysis. Note that this differs from the ablation experiment above: ablation **disables a Harness component** to see how overall performance changes; model swapping **fixes the Harness and changes only the model**. The former locates which part inside the Harness matters; the latter tells you whether the bottleneck is the model or the Harness.

An evaluation system is worth even more in an era of rapid model evolution. Models keep improving, but a new model that scores higher on public benchmarks will not necessarily do better on your task—it may even regress (perform worse than the old version in some respects). Only a full run on your own evaluation dataset lets you make a data-driven upgrade decision. A solid evaluation system even makes **"building products for future models"** a viable strategy: if the current model isn't good enough for commercial deployment, finish the product anyway, build the evaluation set, track each new model's performance, and launch the moment one clears the bar.

A complete evaluation system decomposes into four stages: what counts as success, where the tasks come from, who verifies, and how a score turns into a decision, as shown in Figure 7-1.

![Figure 7-1: The Four Stages of an Agent Evaluation System](images/fig7-1.svg)

## Anatomy of an Evaluation Task: The telecom Domain of τ²-bench

Let us begin by dissecting one real task from the telecom domain of τ²-bench in full. τ²-bench is Sierra's open-source project; clone it locally with the command in `chapter7/tau2-bench-eval/README.md`, then open the task file `data/tau2/domains/telecom/tasks_small.json`.

### The Four Components of a Task Definition

Below is one task from that file, abridged for readability.

```jsonc
{
  "id": "[mobile_data_issue]airplane_mode_on|user_abroad_roaming_enabled_off",

  // The ticket handed to the Agent
  "ticket": "The user is unable to browse the internet and the status bar shows
             'No Service'. Customer John Smith, phone 555-123-2002, currently
             abroad in France. They will consider the issue resolved when the
             speed test returns excellent. They will not change their data plan
             but will refuel 2.0 GB of data if necessary.",

  // The behavioral spec handed to the user simulator
  "user_scenario": { "instructions": {
      "known_info": "You are John Smith with phone number 555-123-2002.
                     You are currently abroad in France.",
      "unknown_info": null,
      "task_instructions":
        "…express mild frustration after the first unsuccessful attempt.
         You will consider the issue resolved only when speed test returns
         excellent internet speed and nothing else. If it returns poor, fair
         or good, you will not consider the issue resolved.
         Whenever the agent asks you about your device, always ground your
         responses on the results of tool calls. …
         Never make up the results of tool calls."
  }},

  // Reset both sides to the same starting point before the run
  "initial_state": { "initialization_actions": [
      { "env_type": "user",      "func_name": "turn_airplane_mode_on" },
      { "env_type": "user",      "func_name": "turn_roaming_off" },
      { "env_type": "assistant", "func_name": "enable_roaming",
        "arguments": { "customer_id": "C1001", "line_id": "L1002" } }
  ]},

  // Scoring criteria
  "evaluation_criteria": {
      "actions": [
        { "requestor": "user", "name": "toggle_airplane_mode" },
        { "requestor": "user", "name": "toggle_roaming" }
      ],
      "env_assertions": [
        { "func_name": "assert_mobile_data_status", "expected_status": true },
        { "func_name": "assert_internet_speed",
          "expected_speed": 200, "expected_desc": "excellent" }
      ],
      "communicate_info": null,
      "nl_assertions": null,
      "reward_basis": ["ENV_ASSERTION"]
  }
}
```

Four design decisions in this definition deserve elaboration.

**The user's knowledge boundary is modeled explicitly.** `known_info` contains only three facts: name, phone number, and country. The two actual causes of the fault — airplane mode is on, data roaming is off — are not among them. The user does not know, and therefore cannot volunteer them; the Agent can only obtain them by asking questions and guiding the user to check. This is how **progressive information disclosure** is implemented at the level of the task definition: not by constraining the simulator with a prompt that says "don't reveal everything at once," but by modeling the user's knowledge as a field of its own. Most benchmarks state the complete requirement at the start of the task, whereas a real user's opening line is often no more than "I can't get online." Clarifying a request until it is actionable is itself part of what an Agent must be able to do.

**The simulator receives a behavioral spec, not a script of lines.** `task_instructions` carries three kinds of constraint: an emotional setting (show mild frustration after the first unsuccessful attempt), an acceptance criterion (the issue counts as resolved only when the speed test returns excellent; poor, fair, and good are all rejected), and a **grounding** requirement — every answer about the device state must be based on the result of a tool call, "Never make up the results of tool calls." The third is the most consequential: without a grounding constraint, the simulated user will follow the Agent's lead and confirm that the problem is fixed, and the evaluation degenerates into two models agreeing with each other.

**The initial state is partitioned by which side controls it.** `env_type` takes two values, `user` and `assistant`: airplane mode and the roaming switch belong to the user's side, while the carrier-side `enable_roaming` belongs to the Agent's side. This partition determines the shape of the fault — roaming is provisioned on the carrier side but switched off on the user's handset, so an Agent querying the database sees nothing but "configuration normal." The fault sits on the side the database cannot see, and only guiding the user to check will surface it.

**Scoring is defined in four layers, and this task uses only one of them.** `env_assertions` checks the final state (mobile data available, speed test at or above 200 Mbps and rated excellent), `actions` checks whether the key actions occurred and **which side performed them**, and `communicate_info` and `nl_assertions` check whether the necessary information was conveyed to the user. This task's `reward_basis` declares only `ENV_ASSERTION`; the remaining layers are still computed and recorded but do not enter the final reward. The scoring basis is declared per task rather than fixed globally.

### The Trajectory of a Real Run

We now ask the reader to run the evaluation tasks of the τ²-bench telecom domain, observe the task design, the user simulator, the process and outcome verification logic, and the Agent's execution trajectory, and analyze why the Agent fails.

> **Experiment 7-1 ★: Run τ²-bench and Compare It with τ-bench**
>
> This experiment runs the τ²-bench evaluation framework to understand the design points of a human-computer interaction evaluation environment. First, read the task definition file along the path taken in this section: each task consists of four parts — known information, task instructions, initial state, and success conditions. Then run the full evaluation flow, observe the multi-turn dialogue between the user simulator and the Agent, and analyze typical failure modes (policy violations, omitted information, excessive escalation to a human agent, and so on).
>
> ![Figure 7-3: Dual-Control Environment and Layered Verification in τ²-bench](images/fig7-3.svg)

The companion repository retains one run record (`chapter7/tau2-bench-eval`). Below we analyze one successful run from it.

The first dozen or so turns are the account identification phase. The Agent looks up customer C1001 by phone number, then queries the data usage of all three lines L1001, L1002, and L1003 one by one, and finally circles back to ask which number the user is actually using in France. In message 17 it reaches an incorrect conclusion:

> **Agent** (17): The number 555-123-2002 is not among your active lines. The closest match is 555-123-2001…

That conclusion rests on a query of line L1001 alone. After the user insists the number is correct, the Agent goes on to query L1002 and finally matches it. The pivotal moment comes at message 30:

> **User** (30) → calls `check_network_status()`, `check_status_bar()`
>
> **Tool returns** (31): `Airplane Mode: ON | Cellular Connection: no_service | Mobile Data Enabled: Yes | Data Roaming Enabled: No`
>
> **User** (33): I see my phone is currently in Airplane Mode, which is why there is no signal. Mobile data is enabled, but data roaming is off. Should I turn off Airplane Mode and try again?

The party issuing the tool call is the **user**, not the Agent. This is the **dual-control** mechanism: the simulated user owns an independent tool set of its own, including `check_status_bar`, `toggle_airplane_mode`, `reseat_sim_card`, and `run_speed_test`.

The remaining troubleshooting goes smoothly: the Agent asks the user to turn off airplane mode and turn on roaming, the user performs both actions (35, 37), and the status bar switches to full-bar 5G; the Agent asks for a speed test, which returns 275 Mbps rated Excellent (46), and the user confirms the issue is resolved. Both `env_assertions` pass and `reward = 1.0`.

This full-marks trajectory also contains a problem the verifier never caught. The opening paragraph of the telecom Agent policy states "You should only make one tool call at a time," yet in message 4 the Agent issued `get_customer_by_phone` and `get_customer_by_name` in a single turn. The verifier did not mark this as an error, because this task's `reward_basis` considers only the final state. This is not an oversight in τ²-bench but the inherent price of a binary reward: it trades process granularity for a single number that is comparable across models. Production evaluation systems, however, usually need more: not only a verdict on whether the outcome is right, but an indication of where the problem lies.

The failed task is equally worth analyzing. The user's number is 555-123-2002, yet the Agent settled on line L1001 and kept reasoning from its 3.2/5 GB usage figure. Along the way, `get_details_by_id(L1001)` explicitly returned 555-123-2001 as that line's number; the Agent read the result but did not revise its judgment, then spent dozens of messages on unrelated diagnostics and finally escalated to a human agent. It did in fact complete half the task — it guided the user to turn off data saver mode, and that user-side action genuinely occurred and was verified by the environment — but the wrong line selection meant the required 2 GB data refuel was never performed, and all three final-state assertions failed. This failure shape closely resembles the AndroidWorld case discussed later in "Failure Attribution": the evidence needed to correct the judgment had already entered the context, and the Agent did not go back on the strength of it.

This one task already poses every question an evaluation set has to answer: what counts as success, where tasks come from, who verifies, and how a score turns into a decision. The following sections take them in turn.

## Evaluation Metrics: Defining Success

The evaluation result in the previous section was four of five tasks passed. The number 0.8 by itself says nothing about whether the system is usable. If it belongs to a refund customer service Agent, it means one user in five does not get the refund they are owed; if it belongs to a security Agent used to hunt for vulnerabilities, hitting four out of five is quite respectable. The difference lies in how high a success rate the business scenario demands.

### Technical Wonders: Capability Ceilings with Pass@k

Many current models and Agents are still in what can be called the **technical wonder** phase. The wonder is a capability ceiling demonstrated under many attempts, a generous time budget, and human selection: one success is enough to prove that the thing is possible in principle. That is exactly the logic of **Pass@k** — run the same task $k$ times and count it as passed if at least one run passes; when the output is a continuous score, take the best run and call it **Best@k**.

Anthropic's discussion of long-running Agents illustrates this kind of ceiling: letting an Agent work autonomously for a week and write a C compiler from scratch; having it explore until it finds a counterexample to an important mathematical conjecture; or having it review open-source software over and over until it surfaces a serious security hole that has been sitting there for decades.

For engineering and research exploration of this kind, what gets demonstrated is usually not "right every time" but a single breakthrough trajectory that finally appears once the exploration budget is stretched far enough. For scientific discovery, vulnerability hunting, and open-ended creative work, that ceiling is valuable in itself: a human can pick the best of $k$ candidate trajectories.

Beyond the foundation-model labs, many application companies use the technical-wonder strategy too. Manus drew wide attention because it handed people a virtual computer, letting an audience with no intuition for Agents discover that AI can operate a computer the way a person does — working for half an hour or an hour and completing a complex task step by step.

OpenClaw gave many people their first sense that an Agent could feel like a live colleague. Users assign it work through an instant-messaging app much as they would a real person; it can reach every file on the computer and every online service, it reports back or asks for more information when it reaches a certain point, and it can even wake itself up to check and handle email.

Early Manus and OpenClaw did not have high success rates on complex tasks, and their token costs were steep. But because these Agent frameworks are general-purpose, complex tasks tend to have a high Pass@k when paired with the strongest models, which is a high technical ceiling. Those technical wonders were shared widely on social networks, and that was the key to these products' success.

### Business Reliability: Focus on Pass^k

Real businesses usually care about the opposite: not a single mistake across repeated attempts. We call this target **Pass^k** (read as **Pass consecutive k**): run the same task $k$ times in a row, require every run to pass, and allow no veto — no safety, compliance, or hallucination violation. It answers "can the Agent deliver reliably" rather than "can it occasionally work a miracle".

If the runs are independent and the single-run success rate is $p$, the relationship between the two metrics is straightforward:

$$
\mathrm{Pass@k}=1-(1-p)^k,\qquad
\mathrm{Pass}^{k}=p^k.
$$

At $p=0.6$ and $k=5$, for instance, Pass@5 $=1-0.4^5\approx99.0\%$ — it looks as though at least one run almost always succeeds. But Pass consecutive@5 $=0.6^5\approx7.8\%$, which says that getting five in a row without a slip is still hard. The first number is the right way to measure a capability ceiling during exploration; only the second comes close to the reliability that payments, refunds, permission changes, and production deployments demand.

An evaluation report must state exactly what the $k$ attempts are: $k$ independent samples of the same task, or $k$ consecutive tasks on a production pipeline. For operations with side effects you cannot simply "retry until it works"; sample in a sandbox or a rollback-capable environment instead, and record every failure in the reliability metric.

## The Evaluation Environment

Once the metric is settled, the next question is where to test. An evaluation environment is an apparatus that can be run repeatedly: given the same initial state, the same Agent should produce comparable results.

### The Five Components

Return to the telecom task dissected above. Taking it as the reference, everything a repeatable evaluation environment requires is already present.

**Dataset** is the task file itself: the initial state, the ticket for the Agent, the behavioral spec for the simulator, and the acceptance criteria are packaged into a single record, and one record is one test case.

**Environment State** is the mutable information during task execution: customers, lines, plans, and bills in the database, plus airplane mode, roaming, the data saver switch, and the remaining data allowance on the device side. It must be resettable, and `initialization_actions` is the reset script. Realism requires state changes to follow business logic; controllability requires that every run start from the same point.

**Tools** belong to two sides. The Agent can call carrier-side operations such as looking up a customer, checking usage, refueling data, and transferring to a human agent; the user can operate the switches on the device. Both tool sets are atomic operations — there is no high-level abstraction such as "solve the user's connectivity problem." Too high a level of abstraction reduces the evaluation to a test of a single function call, with the planning and reasoning absorbed into the tool itself.

**Rubric** is the four layers of checks in `evaluation_criteria`, plus the aggregation rule in `reward_basis`.

**Interaction Protocol** specifies the order of interaction and the termination conditions. Here the normal termination signal is the simulated user emitting `###STOP###`; there is also a turn limit, and the simulated user may end the conversation on its own once its patience runs out — poor communication efficiency counts as a failure in itself.

Remove any one of the five and the evaluation no longer forms a repeatable loop. The same five serve as the reference frame when we examine other benchmarks below.

### Human-Computer Interaction and Tool-Calling Evaluation Environments

Tasks like telecom must have a counterpart to interact with, so the user simulation among the five components is indispensable. Another large class of tasks has no conversational counterpart at all: in code generation, data analysis, and mathematical problem solving, the Agent interacts only with tools from start to finish, correctness is decided by whether execution verification passes, and neither human annotation nor model judgment is required. Such environments dispense with the user simulator; the other four components remain but take simpler forms — the environment state is a file system or a database, the rubric is a piece of test code, and the interaction protocol degenerates into "keep calling tools until an answer is produced or the turn budget is exhausted."

The Verifiers framework stratifies these environments along two dimensions: whether the task needs to maintain state across turns, and whether it needs isolation. `SingleTurnEnv` suits asking a math question and verifying the answer directly; `ToolEnv` suits searching several web pages, synthesizing an answer, and then verifying the final result; `StatefulToolEnv` suits modifying a database record and then verifying the state change; `SandboxEnv` suits running code in a sandbox and then checking the output files. Table 7-1 summarizes these four environment types, making it easy to choose based on task state, tool calling, and isolation requirements.

Table 7-1 Comparison of Verifiers Environment Types

| Environment Type | State Persistence | Tool Calls | Typical Use Case |
|---|---|---|---|
| SingleTurnEnv | None | None | Single-turn Q&A, math problems |
| ToolEnv | None | Multi-turn | Search + information synthesis |
| StatefulToolEnv | Yes | Multi-turn | Modifying database records |
| SandboxEnv | Yes + isolated | Multi-turn | Code execution and testing |

The framework supports parallel sampling and trajectory caching; the complete trajectory of every evaluation (observations, actions, rewards) is saved for later analysis and replay. In addition, a tool's effect depends on the current state, so on failure it should return a clear error message rather than a bare failure flag, allowing the Agent to adjust its strategy accordingly.

Tool-calling evaluation examines the correctness of observable state changes, while human-computer interaction evaluation examines the soundness of the communication strategy — the former verifies action, the latter verifies guidance. Figure 7-2 contrasts the structure of the two environment types.

![Figure 7-2: Tool-Calling and Human-Computer Interaction Evaluation Environments](images/fig7-2.svg)

## Design of the Evaluation Dataset

The evaluation environment is the stage and the dataset is the script. The same five components, applied to a different class of task, may be filled in entirely differently: where the tasks come from, how deeply the verifier can check, and how memorization is prevented. This section starts from the design practice of several public benchmarks and ends with a more practical question — where the tasks in a self-built evaluation set should come from.

### A Cross-Benchmark Comparison of Design Choices

The presence or absence of an interactive counterpart, distinguished in the previous section, is only the first-order difference at the environment level; the divergences at the dataset level reveal the design trade-offs more clearly. Table 7-2 places several frequently cited benchmarks side by side.

Table 7-2 Key Design Choices of Several Agent Benchmarks

| Benchmark | Capability Tested | Task Source | Environment Played By | Verifier |
|---|---|---|---|---|
| τ²-bench | Human-computer interaction and tool calling in customer service | Hand-written + combinatorial generation | User simulator + business database | Four layers of checks aggregated to binary by `reward_basis` |
| SWE-bench Verified | Software development, coding | Real GitHub issues, manually screened | Code repository + test suite | FAIL\_TO\_PASS / PASS\_TO\_PASS dual verification |
| AndroidWorld | Operating the Android phone GUI | Parameterized template instantiation | Real Android emulator | Final UI state assertions |
| OSWorld | Operating the Linux desktop GUI | Started from a preconfigured intermediate state | Real virtual machine | 134 independent evaluation functions |
| Terminal-Bench | Operating the Linux terminal, coding | Hand-written | Docker container | File system checks + real execution |
| GAIA | General-purpose AI assistant gathering information | Hand-written + proprietary attachments | The open internet | Exact string matching |

### Verifiers

An Agent can easily write an expansive report claiming the task is fully complete when in fact nothing of the sort happened. An evaluation framework must verify facts that a machine can check independently, not the Agent's own account of itself.

**SWE-bench Verified decomposes "the fix is complete" into two independent propositions.** One set is FAIL\_TO\_PASS: failing before the fix and passing after it, proving the problem really was solved. The other is PASS\_TO\_PASS: passing both before and after, proving no new defect was introduced. Check only the first and an Agent can slip through by deleting or rewriting the assertions that stand in its way; check only the second and you have checked nothing at all. Only checking both makes "fixed" and "did not break anything" two separately provable conclusions. It additionally confirms the stability of the tests themselves, excluding flaky tests that sometimes pass and sometimes fail.

**OSWorld's verifier can detect cases of superficial completion but substantive error.** It is equipped with 134 independent evaluation functions and full operating system access, able to inspect file system structure, process state, network connections, and application internals. In a database task, the evaluation script not only confirms that the report file exists but also connects to the database to verify that the SQL actually executed; in a browser task it analyzes the DOM tree, inspects cookies and localStorage, and sends verification requests to the backend to confirm that the form really took effect.

**Terminal-Bench**'s task `build-linux-kernel-qemu` requires building Linux kernel 6.9 from source, adding a custom printk in `start_kernel`, generating an initramfs, and running it under QEMU; success is defined as the custom message appearing in the boot log. The Agent cannot fabricate the output — it has to complete the whole process for real.

### Difficulty Stratification of Tasks

An evaluation task set needs tasks at different difficulty levels. That way the set does not go stale quickly as model capability improves.

The full GAIA set of 466 questions is divided into three difficulty levels: Level 1 requires only one or two tools (humans 93.9%, GPT-4 30.3%), Level 2 requires multi-step reasoning (91.8% versus 9.7%), and Level 3 requires complex composition (87.3% versus 0%). This stratification does more than label difficulty; it has diagnostic value. A Level 1 failure points to basic tool use, Level 2 to multi-step planning and information integration, and Level 3 to long-sequence reasoning and complexity management, and the three imply different directions for improvement.

Terminal-Bench spans everything from simple MLflow model registration, to medium-difficulty 7-Zip password cracking, to difficult multi-component integration of a Git server and a web server, up to the hardest FEAL differential cryptanalysis.

τ²-bench additionally designs **trap tasks**, in which the user claims "customer service has already approved the cancellation" when it does not in fact comply with policy, testing whether the Agent holds its judgment under pressure and misdirection.

### Preventing Data Contamination

**GAIA makes its answers impossible to retrieve directly from the internet.** Its tasks are conceptually simple with open paths — for example, starting from NASA's Astronomy Picture of the Day for a given date, identifying the astronaut in the image, finding the astronaut group they belonged to, computing which member of that group spent the least time in space, and formatting the output strictly as "last name; semicolon-separated; thousands separators." The answer is highly specific, and correctness is decided by exact string matching. Leakage prevention rests on two things: first, the question can only be answered by combining several information sources, so no single web page gives the answer directly; second, some tasks come with specially produced attachments (PDFs, audio, and images that do not exist on the internet).

**AndroidWorld derives a large number of instances from a single template.** Its tasks are not static text but dynamically instantiable templates such as "change the phone number of contact `[CONTACT_NAME]` to `[NEW_PHONE]`," with parameter values generated randomly for each evaluation. This yields three benefits: parameters differ each time, so replaying a fixed action sequence is useless; a single template can generate a nearly unlimited number of instances; and fixing some parameters while varying others allows the effect of a specific factor to be measured precisely.

**Terminal-Bench embeds a canary identifier in the task statement.** Every task carries a canary GUID; if a model can output content containing that GUID, the benchmark data has entered the training set. It does not prevent leakage, but it makes leakage detectable.

### Quality Control and Long-Term Maintenance

Building a high-quality evaluation set is very hard. The present form of most of the benchmarks above is the result of round after round of repair once the first version was put to use and its problems surfaced. From τ-bench to τ²-bench, for instance, there are five places where the design was reworked.

First, **task instructions were too vague, letting the answer be guessed**. The first version's task instructions were written broadly, so the model did not need to genuinely clarify the requirement — guessing a plausible workflow from common sense was enough to pass. τ²-bench split the script into two fields, `known_info` and `task_instructions`: the former delimits what the user knows, the latter prescribes how it is disclosed. What the user does not know, the Agent cannot guess and can obtain only by querying.

Second, **success conditions were not precise enough, causing verification errors**. A condition such as "the network is back" has no checkable boundary. τ²-bench changed it to "the issue counts as resolved only when the speed test returns excellent; poor, fair, and good are all rejected." This change targets **perfunctory fixes**, which suppress the symptom without addressing the root cause.

Third, **the user simulator behaved too mechanically**. The first version's simulated user only responded passively. τ²-bench added emotion (showing displeasure after the first failed fix), a patience limit (ending the conversation when communication efficiency is too low), and the grounding requirement. Together these make the simulator approximate a real user while remaining reproducible.

Fourth, **the user participates not only in the conversation but also in the operation**. The telecom domain introduced a dual-control environment. In earlier evaluations only the Agent could change the environment, whereas in technical support scenarios a substantial share of the actions ought to be performed by the user on their own device. Dual control also adds a dimension to verification: after the user changes the state, the Agent must call a tool again to learn the result, so verification now covers whether the Agent actually read the outcome of the user's actions.

Fifth, **task instances are generated dynamically**. τ²-bench's concrete instances (user names, phone numbers, fault combinations) can be generated in bulk from parameters, which improves both coverage and resistance to leakage.

**SWE-bench Verified: 71% of the original tasks were eliminated before release.** OpenAI randomly sampled 1,699 of the original 2,294 tasks for human evaluation, recruiting 93 developers proficient in Python to check each one: whether the problem description was clear, whether the test cases covered edge conditions, whether the tests were stable, whether the reference patch introduced new errors, and whether the difficulty was reasonable. In the end only 500 passed. The high elimination rate buys a better signal-to-noise ratio, and evaluation cost drops by roughly 80% as well. Complex Agent tasks routinely take minutes to hours, and running a full evaluation dataset with a frontier model often costs thousands of dollars in tokens, so reducing evaluation cost matters a great deal.

**OSWorld: more than 300 issues surfaced in the 15 months after release.** Released in April 2024, it quickly became an important benchmark for multimodal Agent evaluation, and widespread use then exposed four categories of problems: environment issues (anti-scraping measures, CAPTCHAs, dynamic content changes), task description issues (ambiguous phrasing), verification logic issues (too strict or too lenient), and initial state issues (incomplete configuration). A team of about ten people from the University of Hong Kong worked closely with MoonShot AI, OpenAI, ByteDance Seed TARS, Anthropic, Simular, and others for two months on a systematic repair: environment issues were resolved by locking versions and keeping offline backups, description issues by rewriting ambiguous phrasing, verification issues by manually establishing correct baselines and adjusting conditions, and initial state issues by adding completeness checks.

> **Experiment 7-2 ★: Manually Execute Benchmark Tasks**
>
> Select tasks from GAIA, AndroidWorld, SWE-Bench Verified, Terminal-Bench, and OSWorld-Verified and complete them by hand; one easy, one medium, and one difficult task per dataset is recommended. The "difficult" level is challenging for humans too.
>
> Afterwards, answer two questions. Does the task description admit more than one reasonable interpretation, and if so, which one does the verifier accept? If you tried to slip through without doing the work, what would the cheapest path be, and could the verifier stop it?

### Three Sources of an Evaluation Set

A common view holds that public benchmarks serve model ranking and have limited bearing on real business. It is true that public benchmark scores are hard to translate directly into product decisions, but their design techniques transfer perfectly well. Verification depth, parameterized generation, leakage prevention, and quality maintenance — the topics discussed above — are precisely the places a self-built evaluation set is most likely to neglect.

An evaluation set in production usually has three sources.

**Public benchmarks** are used for coarse model screening and for borrowing design techniques, and generally not for product decisions. Their task distribution does not match that of your business; gaining two percentage points on GAIA bears no necessary relation to your refund success rate.

**A self-built business set** covers the real task distribution and can serve as the basis for model selection and Harness design decisions. τ²-bench, for example, can serve as the skeleton for any evaluation system that needs a simulated user; you only have to substitute your own domain data and tool set.

**Production trajectory feedback** comes from real failures in the field: cases where the user explicitly corrected the Agent, where the user gave a thumbs-down, and where a subsequent state check, rule-based verifier, or LLM review found a problem. After failure attribution, these settle into regression cases. The concrete method is described later in "Failure Attribution" and "End-to-End and Trajectory-Prefix Regression Tasks." This source is the most expensive and also the most accurate, because it comes directly from what users actually encountered.

In the early stage there are usually only public benchmarks and a small hand-written business set; once the system has been running in production for a while, cases fed back from production trajectories become the main body.

## Automated Evaluation Methods

The benchmarks discussed in the preceding sections have one thing in common: their verifiers are almost all deterministic. SWE-bench runs a test suite, AndroidWorld asserts the final UI state, GAIA does exact string matching, and τ²-bench's four layers of checks are likewise executed entirely in code. There are good reasons for this choice: deterministic verification adds no model overhead, results are fully reproducible, it can be folded into continuous integration like a unit test, and it makes ranking across models straightforward.

The price is that it can only judge whether the final outcome is right; it cannot give the reason for an error. The failed τ²-bench task above scored 0, and that 0 says nothing about whether the Agent went wrong at line selection or skipped the data refuel step, still less about what to change next. For a public benchmark used for ranking, this is not a defect; for a production system that needs continuous improvement, it is exactly the information most needed.

Production scenarios face a second difficulty: many judgments simply cannot be written as assertions that code can check. Whether a complaint response is appropriately worded, whether a research report omits a critical piece of information, whether a memory retrieval got a relationship between people wrong — none of these has a unique final state to query, nor can they be decided by keyword matching.

Moving from public benchmarks to evaluation in production therefore requires the mode of verification to shift rightward along a spectrum whose horizontal axis is the **degree to which a task is mechanically verifiable**, as shown in Figure 7-4.

![Figure 7-4: A Spectrum of Verification Modes, from Deterministic Verification to Model Judgment](images/fig7-4.svg)

The two instruments on the right of the spectrum consequently become the mainstay of production evaluation: a **Rubric** that breaks the vague question of "how good is it" into several separately scorable dimensions, and **LLM-as-a-Judge** that produces the score where no deterministic criterion exists. Only together can they turn a blanket failure rate back into concrete, fixable problems; combined with **failure attribution** in the second half of this section, they form the complete evaluation loop for a production Agent.

It should be said that moving rightward does not mean abandoning the left. Every check that can be written as a programmatic assertion should stay an assertion, and LLM judgment should be reserved for the dimensions that genuinely cannot be decided mechanically. Deterministic checks are cheaper and more stable, and they are far better suited to running as regression tests over the long term.

### LLM-as-a-Judge: The Core of Automated Evaluation

![Figure 7-5: LLM-as-a-Judge Pipeline](images/fig7-5.svg)

Why is LLM-as-a-Judge needed? For open-ended tasks (e.g., generating reports, handling customer complaints, creative content), there are no standard answers for automatic comparison, and human evaluation is costly and difficult to scale. LLM-as-a-Judge balances the scalability of automation with human expert judgment by having a language model evaluate outputs against expert-defined scoring criteria (a Rubric).

The method has known limitations, though: the judge model carries its own biases, and repeated judgments of the same input can vary. The most typical is **length bias**, a tendency to score longer, more detailed responses higher even when they are no more correct — much as a human sitting an exam will pad out an answer they do not know, hoping to stumble onto a point or two. Three defenses are common: penalize verbosity explicitly in the Rubric and cap response length per task type; in pairwise comparisons, bring the two candidates to similar lengths before judging; and regularly audit the correlation between scores and response length — if high scores almost always go to long responses, the judge has been swayed by length and the Rubric needs revision. To address these challenges systematically, Rubric design must follow the principles below:

**Rubric (Scoring Criteria): The Basis for LLM Judgment.**

**Four Rubric Principles** (Scale AI, "Rubrics as Rewards"):

(1) **Based on Expert Guidance**—A Rubric must reflect domain knowledge, capturing the core facts and reasoning steps. A Rubric for medical Q&A, for instance, needs diagnostic criteria and the medical errors that must be avoided; one without expert grounding can only capture surface features like fluency.

(2) **Comprehensive Coverage**—A Rubric should cover factual accuracy, logical coherence, completeness, and safety. It should not only define positive standards but also explicitly identify **Pitfalls**—i.e., high-risk common errors, such as recommending unverified therapies in medical advice.

(3) **Standardized Importance Weighting**—Classify criteria as Essential, Important, Optional, or Pitfall items. The scheme supports a **Veto mechanism**: for example, in a customer service scenario, hallucination (fabricating false information) is a typical veto dimension—regardless of how well other dimensions perform, if false information appears, it must be vetoed. This also helps prevent reward hacking through keyword stuffing.

(4) **Self-Contained Evaluation**—Each evaluation item is independently actionable and does not rely on the evaluator's domain knowledge. Abstract standards like "the response demonstrates deep understanding" should be avoided, replaced by verifiable standards like "cites at least two authoritative theories and accurately explains how they support the conclusion."

The key practice: define objectively verifiable scoring levels for each dimension, with concrete examples and **edge cases** to resolve ambiguous situations. Actively guard against **Reward Hacking**—the Agent finding a "shortcut" to high scores without actually completing the task—by explicitly penalizing hallucination, sycophancy, keyword stuffing, and dodging hard questions. A Rubric is an iterative product: trial use reveals disagreements among evaluators, and the Rubric gradually evolves through this feedback from abstract principles into a detailed casebook.

Here is a complete Rubric that follows the four principles, using a user memory Agent as the example. Test question: "Who is my daughter's pediatrician?" (The answer requires linking information across two conversations: the first conversation mentions "my daughter's name is Lily," the second mentions "took Lily to see Dr. Chen").

```yaml
rubric:
  dimensions:
    - name: Factual Correctness
      weight: essential        # Essential item
      scoring:
        4_Excellent: "Correctly answers Dr. Chen, and links to daughter Lily"
         3_Good: "Correctly answers Dr. Chen but does not mention that Dr. Chen is Lily's doctor"
        2_Passable: "Gives the correct doctor but with additional uncertain information"
        1_Fail: "Gives an incorrect doctor's name, or answers 'I don't know'"

    - name: Information Completeness
      weight: important        # Important item
      scoring:
        4_Excellent: "Proactively supplements relevant information (e.g., last visit date, diagnosis)"
        3_Good: "Answers the core question without omission"
        2_Passable: "Answers the core question but omits available related information"
        1_Fail: "Key information is missing"

    - name: Reasoning Correctness
      weight: important
      scoring:
        4_Excellent: "Correctly links the two cross-session pieces of information: 'daughter=Lily' and 'Lily's doctor=Dr. Chen'"
        3_Good: "Correctly links but the reasoning path is not clear enough"
        2_Passable: "Partially correct linking"
        1_Fail: "Incorrect linking (e.g., mistaking the user's own doctor for the daughter's doctor)"

    - name: Hallucination Detection
      weight: veto             # Veto item: once triggered, total score is zero
      scoring:
        pass: "All information can be traced back to historical conversation records"
        fail: "Fabricated information not present in the conversation (e.g., fictitious visit dates, diagnoses)"

  edge_cases:
    - "If the user has multiple daughters who see different doctors, should ask which daughter"
    - "If the memory contains both 'Dr. Chen' and '陈医生' (the same name written in Chinese), should recognize them as the same person"
```

**Good Rubric vs. Bad Rubric**: Each scoring level above specifies verifiable, concrete behavior ("Correctly answers Dr. Chen") rather than descriptions that cannot be judged objectively, like "demonstrates a deep understanding of memory." The veto item sets the bottom line: even if every other dimension scores full marks, a single instance of hallucination results in an automatic zero.

Give the judge both the Rubric and the Agent's response. It will score each dimension and explain why. Once results from dozens of cases are grouped by dimension and the low-scoring traces are replayed, a vague drop in success rate becomes a concrete diagnosis: retrieval missed a fact, the model linked the wrong people or events, or it added an unsupported claim. A useful Rubric tells the team not only how the system scored, but where to look next.

The following takes user memory as a concrete case, showing how to bring this general method down to an executable evaluation set and verifier.

> **Experiment 7-3 ★★: Building a Rubric-Based User Memory Evaluation System**
>
> **Prerequisites**: Must complete the Chapter 3 User Memory Experiment (`chapter3/user-memory-evaluation`).
>
> This experiment requires modifying the `chapter3/user-memory-evaluation` framework from Chapter 3, upgrading the current simple LLM-as-a-Judge scoring mechanism to a structured, multi-dimensional Rubric evaluation system. The existing system uses a single LLM call to return a pass/fail result plus evaluation reasoning, lacking structured diagnostic capabilities.
>
> Design a unified multi-dimensional Rubric framework applicable to all three task levels. Evaluation dimensions include: Factual Correctness (precision: of all the information given, how much is correct—verifies that numbers/dates/names are consistent with the stored memory); Information Completeness (recall: of all the information that should be given, how much is mentioned—verifies that all relevant information is provided with no key content omitted); Reasoning Correctness (checks whether the relationships between pieces of information and implicit logic are correctly understood); Reasoning Proactiveness (evaluates whether suggestions or risk warnings beyond a direct answer are provided when appropriate); Hallucination Detection (ensures no information not present in memory is fabricated).
>
> Four-level scoring (Excellent/Good/Passable/Fail), with specific judgment criteria for each level rather than abstract descriptions. The hallucination dimension is a veto item. Provide examples and boundary cases for each dimension.
>
> **Experiment 7-4 ★★: Comparative Evaluation of Advanced JSON Cards vs. RAG**
>
> **Prerequisites**: Must complete the Chapter 3 User Memory and RAG experiments (`chapter3/user-memory`, `chapter3/agentic-rag-for-user-memory`).
>
> **Objective**: Fairly compare the advantages and boundaries of structured memory versus unstructured retrieval on the same evaluation set. Reuse the two Chapter 3 projects and compare three configurations on the 60 test cases from `chapter3/user-memory-evaluation`—Pure Advanced JSON Cards (structured cards kept in context, with no retrieval needed), Pure RAG (conversation chunks embedded in a vector store, retrieval required), Hybrid System (core facts resident + original conversations retrieved on demand).
>
> **Acceptance Criteria**: Record success rate, average steps, number of tool calls, latency, and cost across three complexity levels (basic recall / multi-session disambiguation / cross-session hidden associations). Clearly describe the failure boundaries for each approach—what structured memory misses, what retrieval misses, and whether the hybrid truly achieves synergy. This is an **end-to-end regression layer**: it checks that the complete task still works, but cannot by itself show whether the Agent correctly scopes a memory once it has been supplied. Configuration details and test cases are available in the companion repository.
>

The companion experiment ran all three systems on the same 60 questions and retained 180 real API trajectories. Table 7-3 reports both the rates and the underlying success counts.

Table 7-3 Success Rate by Memory System and Task Level

| System | Basic Recall | Multi-Session Disambiguation | Hidden Cross-Session Links | Overall |
|---|---:|---:|---:|---:|
| Advanced JSON Cards | 95% | 60% | 50% | 68.3% (41/60) |
| RAG | 90% | 40% | 15% | 48.3% (29/60) |
| Hybrid | 80% | 70% | 50% | 66.7% (40/60) |

Most notably, the hybrid did not win by default. It did on 3 questions what neither single approach managed, yet fell short of the better single approach on 8 others; compared with the best single approach on each question, its average success rate was in fact lower. Pure RAG was not far from structured cards on basic-recall questions, but on cross-session association questions its success rate dropped to 15%. Another easily overlooked figure: across 180 judgments, the hallucination veto fired 28 times—evidence of how much a single veto item matters.

**The Same-Family Model Problem and Multi-Source Judging.**

When the Agent and the judging model come from the same family, the Agent may learn to exploit the judging model's preferences and blind spots.

**This is precisely what Goodhart's Law states: when a metric becomes an optimization target, it ceases to be a good metric.** The more an Agent is trained or tuned on a particular scoring system, the more it tends to exploit loopholes in that system rather than genuinely improving its capabilities.

More insidiously, the Agent will gradually learn to avoid the types of errors that the judging model is not good at detecting, making the scoring system appear perfectly fine.

The mitigation is **multi-source heterogeneous judging**—independent judges drawn from different model families (if the Agent runs on Claude, judge with GPT-5 and Gemini). Different families' biases are often orthogonal, so the Agent can rarely fool all the judges at once. Use the same Rubric so everyone judges the same target, and aggregate by weighted averaging or consistency checks. In deployment, a single model can handle rapid evaluation, with periodic quality audits run against the full multi-source setup.

Multi-source judging addresses the question of which models should serve as judges; the next question is which modalities should be evaluated—extending LLM-as-a-Judge from text to speech, images, and video is another axis of evaluation coverage.

**Multimodal LLM-as-a-Judge.**

Multimodal judging extends LLM-as-a-Judge to the domains of speech, images, and video. Four common directions are as follows.

- **TTS Evaluation** (TTS stands for Text-to-Speech): Assesses accuracy, naturalness, voice consistency, and emotional expression. These dimensions can capture prosodic issues that traditional WER (Word Error Rate) struggles to detect.
- **ASR Evaluation** (ASR stands for Automatic Speech Recognition): Performs semantic impact assessment—misrecognizing "today's weather" is harmless, but misrecognizing "transfer one thousand" as "ten thousand" could have serious consequences.
- **UI Evaluation**: Uses a **Proposer-Reviewer** mechanism to check for issues like text overflow, color contrast, and button placement. Here, the proposer-reviewer is used as an **evaluation method**, differing from its use as a **generation system component** in Chapter 5, but the core mechanism is the same—one model generates, another independently reviews.
- **Video Editing Evaluation**: Verifies the correctness of clip start/end points and effect application through keyframes.

> **Experiment 7-5 ★★: Building a Fully Automated TTS Quality Evaluation Pipeline**
>
> This experiment requires designing and implementing a complete multimodal LLM-as-a-Judge TTS quality evaluation system from scratch.
>
> Design a multi-dimensional TTS Rubric: The Accuracy dimension verifies whether all text is correctly read (no omissions/misreadings/additions); the Naturalness dimension assesses whether the speech sounds natural rather than robotic, has no unnatural pauses, and uses natural prosody; the Emotional Expression dimension checks whether the tone matches the text's emotional tone (rising intonation for questions, emphasis for exclamations, slower pace and lower pitch for sad content); the Voice Consistency dimension evaluates speaker similarity when a reference voice is available (the multimodal model simultaneously receives the reference voice and the synthesized voice for comparison).
>
> Build a diverse test corpus: varying lengths (single sentence → long paragraph), genres (news/story/dialogue), emotions (neutral/excited/sad), and special challenges (numbers/proper nouns/polyphonic characters/dialectal vocabulary). Connect the TTS module to mainstream services (OpenAI, ElevenLabs, Fish Audio, Minimax, Doubao), then send the synthesized audio, source text, reference audio, and Rubric to an audio-capable multimodal judge. Record the judge model and hashes of both candidate and reference audio so that every score can be audited.
>

The companion repository preserves a small direct-listening run. OpenAI and Fish Audio each generated four clips covering numbers, polyphonic Chinese characters, long-form text, and excited delivery; Voxtral completed all eight four-dimensional judgments. Both systems averaged 5.00 for accuracy and 4.00 for naturalness. Fish Audio scored 4.00/3.00 for emotion and voice consistency, while OpenAI scored 3.75/2.75. Splitting the Rubric into dimensions therefore exposed differences that a simple "was it read correctly?" check would miss.

Those scores do not establish a provider winner. There were only four clips per provider, and the fixed reference clip came from Fish S1, which naturally favors Fish Audio on voice similarity. A general TTS comparison should remove that dimension or give every candidate an appropriate target speaker. A voice-cloning comparison should ask every system to imitate the same speaker and calibrate the model judge against blinded human listening. **Choosing the reference answer, image, or audio is part of evaluation design, not neutral setup work.**

Handwritten Rubrics are a fast way to establish diagnostic dimensions like these. At larger scale, a specialized **generative reward model** can automate the judging; Chapter 8 covers how such reward models are trained.

The score a judge model gives says only whether the outcome was good or bad; to turn that outcome into a fixable problem, you still have to locate the step at which the failure actually began.

### Failure Attribution: Locate the First Error in a Trajectory

End-to-end evaluation often says only "pass" or "fail". To make results drive fixes, perform **failure attribution** for every failed trajectory: record the main error class, the first step at which unacceptable behavior appeared, the relevant tool call or model output, and evidence that can be audited. Attribute the first error that sent the task off course; later errors are often just the chain reaction.

Production bad cases usually come from three signals: an explicit user correction ("do not do that"), a downvote or other negative feedback, or a later state check, rule verifier, or LLM judge showing that the Agent did something it should not have done. LLMs can help with this work, but cannot replace careful human reading because failure attribution often reveals product problems, not only technical bugs.

Building a failure-attribution system takes patient reading and analysis of production bad-case trajectories. An LLM can help with the work, but cannot replace the human, because **failure attribution often surfaces product problems**, not just technical ones.

As the product matures, the taxonomy can grow into several top-level classes, each with sub-classes, until it holds hundreds of entries. Those classes and their attribution recipes then become the prompt or the Skill for an attribution-annotation Agent.

For a Coding Agent, a workable initial taxonomy looks like this.

| Error class | Typical symptom | How to locate the first error |
| --- | --- | --- |
| Requirement understanding and ambiguity | What got built is not what the user asked for: a condition in the requirement is dropped, or the scope is read too broadly or too narrowly; when the repository holds two config files with the same name, one is simply picked, with no note and no question | Use an LLM to compare the original requirement against what the Agent **actually did** (the action sequence), item by item; find the first divergence in the outcome, then trace back to the tool call or the reply that caused it |
| Missing process or convention | Committing without running unit tests; editing code before writing a plan; pulling in an external dependency when the repository already has an internal equivalent; bypassing an established architectural convention | Find the first action that violates the development-process convention — the first `git commit`, the first file write — and check whether it had read the source of that convention beforehand |
| Tool-call errors | Repeated failed edits to the same file; malformed JSON/schema or arguments; special characters breaking transcription, escaping, or writing | Record the first failed edit or tool call together with the original request and the error return; repeated failures are downstream symptoms |
| Hacking the verification environment | Editing an assertion, adding a `skip`, mocking out the logic under test; claiming "the tests pass" without ever running them | Take the first message that modifies a test or the verification logic; then cross-check the completion claim against the commands actually executed in the trajectory to confirm whether it really ran |
| Incomplete edit | The function signature changed and three call sites were updated, but a fourth — a dynamic call, a binding in another language, a schema — was missed | Take the set difference between the blast radius the Agent claimed and the real one, pick the first omission, and look back at the keywords it searched with |
| Wrong information reported to the user | Tool calls and environment state are all correct, but what the user is told is not: a wrong amount, status, or time; partial completion described as full completion; a required disclosure omitted |Align every factual claim in the reply against the tool return values and take the first claim that cannot be traced or that contradicts a return |
| Non-functional regression | A public API or schema changed with no database migration script; a validation deleted so that a check would pass | Take the first message that made the change and see whether it recognised that it was touching a public interface or a structure that needs migration |
| Abnormal model termination | Output truncated mid-stream, stopping for no reason, timing out, or ending without the closing action | Locate the first abnormal termination and separate model stop, Harness timeout, and tool-service failure |
| Stopping the task too early | Only part of a multi-goal task is done; declaring something impossible without exhausting the reasonable options | Locate the first decision that dropped a goal or abandoned exploration, and record it separately from the final verification failure |

**An attribution-annotation Agent can use an LLM to run root-cause analysis over production trajectories at scale**, but it must not emit a single sentence of "reason for failure". **The attribution record has to be structured** — JSON or YAML, citing specific step numbers, tool names, and observed evidence; it must also separate root cause from consequence, judge recoverability, and give a confidence. For example, `edit_file` returns an `old_string` mismatch and the Agent then retries three times without writing the file: the primary cause is the file-edit and tool-call error, and the three retries are consequences, not three independent root causes. When several classes appear at once, pick the primary one by the rule "earliest, and explains the failures that follow", and keep the rest as secondary. At least three classes in the table above can be pre-filtered by rules before an LLM is asked to localize the first error: cross-checking the completion claim against the commands actually executed, whether the diff touches test assertions and `skip` markers, and whether the diff changes a public API or schema with no migration file. Rules first, LLM second, is both cheaper and more accurate than feeding every trajectory to an LLM.

When storing an attribution record, keep more than the LLM's output: save the task goal, the environment state, the Agent version, the toolset version, and the complete Agent trajectory, so that the case can be turned into a regression test.

The three classes below are worth a closer look.

#### The "Right Actions, Wrong Report" Problem

"Right actions, wrong report" is the category most often hidden by an overall pass rate, because most evaluations assert only on environment state. τ²-bench scores it separately: of the 704 published baseline runs whose task carries a communication requirement, 240 failed, 162 of those failed the communication check, and 80—a third of all failures—had correct environment state and a wrong report.

The companion repository holds a matching case. Asked to enter the expenses from `expenses.jpg` into a bookkeeping app, the Agent spent 32 steps granting permissions, searching, opening the image, filling in each row and saving, **with no step returning an error**, then declared the task complete; the validator reported that the row it should have written—`Dress`, ¥436.35—was absent, bearing no relation to the four it entered. Step 8 of its own reasoning reads *"I cannot actually see the content/details of the expenses in the image"*: it already knew the data was missing, neither stopped nor reported it, and by step 11 four invented expenses had appeared in its notes, which every later input faithfully entered. The first error is step 8, and that step neither raised an error nor was a tool call. Its root cause is also easy to misfile: T3A is a text-only Agent whose observation space holds only the element tree and no image pixels, so the cause is not "the model cannot do OCR" but a missing observation channel plus the absence of a legal "information unavailable" exit. File it as a model-capability problem and the next move is to swap models or train OCR; the real fix is to add the channel and the exit.

> **Experiment 7-6 ★★: Failure Attribution on AndroidWorld Traces**
>
> This experiment practices the attribution method of this section on real traces, with no emulator and no model API required. The material is the saved T3A run in `chapter7/android-world`: `t3a.md` holds the step-by-step `Action`/`Reason`/`Summary` for every task, and `t3a_failed.md` collects more than fifty failed traces, each ending with the validator's objective verdict.
>
> Step 1: Sampling. Draw at least ten silent failures from `t3a_failed.md` — traces with no tool error anywhere. No tool return may have failed; the Agent either declared completion or ran out of steps; and only the closing validator verdict marks the task failed.
>
> Step 2: Locate the first error. For each trace, record the step number of the first error and whether that step is a tool call or an assistant message. Silent failures need two techniques: fact-anchor comparison, which walks the Agent's statements against the tool return values and takes the first divergence; and trajectory-prefix bisection, which cuts the trajectory at step k and hands it over — if it is still recoverable, the error lies after k. Searching for error keywords is no substitute.
>
> Step 3: Write structured records. Emit one JSON or YAML record per trace with the task name, first-error step, error category, responsible party, supporting quotations, and a separation of primary cause from consequence.
>
> Step 4: Compare with the existing notes. Check your results against `t3a_failed_analysis.md` and record every disagreement. Pay particular attention to root-cause assignment: those notes originally recorded the image-transcription failure as "the vision model lacks OCR," yet T3A's observation space contains no image pixels at all, so the real root cause is a missing observation channel. An existing attribution note is not an answer key.
>
> Step 5: Convert to regression tasks. Take three traces whose first error is an assistant message, cut each trajectory prefix just before that error, and write the acceptable-action set and the forbidden actions to form trajectory-prefix regression tasks.
>

#### Scope-Sensitive Document Formatting Errors

When a user says "the quotes are wrong", that cannot be turned into a global character replacement. At minimum you must distinguish ASCII straight quotes (`"`, `'`), Chinese curly quotes (`“”`, `‘’`) and Markdown backticks (`` ` ``). The same character plays a different syntactic role in Chinese prose, quoted English source, inline code, code blocks, code comments, JSON and paths.

Evaluation data should first parse the document into scoped spans—for example `ZH_PROSE`, `EN_PROSE`, `QUOTED_SOURCE`, `INLINE_CODE`, `CODE_BLOCK`, `CODE_COMMENT` and `JSON_OR_SCHEMA`. Each span records the set of permitted transformations, the characters that must be protected, and the validator result after editing. The three cases below cannot be handled by one replacement rule:

```text
Chinese prose: call the `reset()` method.
Quoted English source: “Please restart the service.”
# the code block below only illustrates a protected scope
# Chinese comment: display "current status"
name = "status"
```

Trajectory-prefix regression should require the model to make the minimal edit, and check at the same time Chinese document style, the preservation rate of quoted English source, code and JSON syntax, and the edit distance over non-target text. When the rules cannot determine the scope, keeping the original text and asking for clarification should count as a permitted action, not a guessed edit that happens to pass.

#### Exact-Copy Errors: From `old_string` Mismatch to Layer-by-Layer Localization

An `old_string` failure cannot be attributed simply to "the model copied it wrong" either. For the same string, store the raw byte hash, the Unicode code point sequence and the tokenizer token ID sequence, then look for the first divergence along this chain:

```text
original file bytes → tool return → Harness serialization → model context
→ model token output → decoded string → JSON/tool-call parsing → tool matching
```

A minimal set of evaluation probes covers direct restatement, extraction from a long context, placement into tool arguments, selection among similar strings, and spaces, newlines, backslashes, Unicode combining characters and low-frequency tokens. The metrics are byte-exact match, code-point-exact match, token-exact match, the position of the first divergence, and the real tool success rate. If the model is correct on the direct probe but the tool call still fails, fix the tokenizer, the serialization, the Harness or the tool protocol; only when the first divergence appears in the model's own output should the case be turned into the copying training data of Chapter 8.

### End-to-End and Trajectory-Prefix Regression Tasks

Once the first error is known, turn the repair target into a repeatable **regression task**. End-to-end regression starts from the initial state and user request, runs the whole workflow, and checks final state, required output, and safety. A **trajectory-prefix regression task** freezes the context, conversation, tool returns, and environment state just before the first error, then tests only the next one or few observable actions. It is cheaper and isolates one decision boundary, so it is especially important for high-reliability production Agents.

**End-to-end regression tasks** start from the initial state and the user request, let the Agent complete the whole task, and check the final state, the required output, and the safety conditions. They come closest to the production result, but make it hard to tell at which step the failure occurred. As a rule, end-to-end regression tasks verify that the Agent's capability in each domain still meets expectations. The standard benchmarks described in this chapter — OSWorld, AndroidWorld, tau-bench — are all end-to-end regression tasks.

**Trajectory-prefix regression tasks** freeze the existing context, dialogue, tool returns, and environment state, and ask the Agent only to think and take the next observable action or few actions. They cost less and isolate a single policy or tool problem. For a production Agent that needs high reliability, building the trajectory-prefix regression set often matters more than the end-to-end one — and it requires the developer to patiently build the failure taxonomy and attribution system described in the previous section.

The answer to a trajectory-prefix regression task should be defined as an **acceptable action set** rather than a single canonical action or answer: it may require "read the repository rules first," "ask the user first," or "refuse the dangerous operation," while also listing the prohibited actions.

**Once failure attribution is done, an evaluation dataset of both end-to-end and trajectory-prefix regression tasks can be constructed.** For a Coding Agent: a missing process should yield an end-to-end regression task carrying a plan document and test acceptance conditions; a tool-call error should have its failing prefix truncated and edited into a boundary task that tests whether the model can fix the format, escape special characters, or switch to a suitable tool; abnormal termination should add recovery scenarios for truncation, timeout, and tool failure; completion and logic errors should add multi-goal checklists, reminders of remaining work, and the "not yet proven impossible" boundary; requirement-understanding and ambiguity cases should freeze tasks with several reasonable readings into prefixes and put "clarify first" in the acceptable-action set; symptom-fix and faked-verification cases should add two hard constraints to acceptance — "test assertions may not be modified" and "a completion claim must carry the output of a command that really ran"; and information-reporting cases should assert on the content of the reply itself, not only on the environment state.

The evaluation dataset is the foundation for the post-training of Chapter 8 and the self-evolution of Chapter 9.

> **Experiment 7-7 ★★: Trajectory-Prefix Boundary Evaluation with Multiple Encodings**
>
> This experiment supplies the Agent with known user memory, the current instruction, a trajectory prefix, tool returns, and environment state, then asks for only the next observable action. It covers production bad cases such as scope conflicts, stale preferences overriding current instructions, low-confidence inferences, confirmation before high-risk deletion, and preview before external publication. The same cases are encoded as JSON Cards, Markdown, and Python-like memory; deterministic checks score the allowed decision category, safety, required evidence, and forbidden actions.
>
> With GPT-5.6-sol through OpenRouter, all 33 cells (11 cases × 3 encodings) completed without API errors. Each encoding passed 6/11 cases, but their failure locations differed, showing that changing the representation alone does not repair application policy.

In practical model selection, we often face the question: "Which is better, A or B?" Pairwise comparison provides an evaluation method that does not rely on absolute scores.

### Pairwise Comparison and Model Ranking

![Figure 7-6: Elo Rating and Pairwise Comparison Ranking](images/fig7-6.svg)

**Elo Rating** (a ranking system originally designed for chess) quantifies the relative ability of models through a large number of pairwise matchups: the larger the rating difference, the higher the expected win rate for the stronger model. For example, if Model A has a rating of 1200 and Model B has a rating of 1000, the Elo system would predict A's win rate to be approximately 76%. If B unexpectedly wins, B gains more points and A loses more—an upset triggers a larger correction, which is what lets rankings converge quickly on true ability. The statistical foundation is the **Bradley-Terry model**: each model is abstracted as a latent "strength score," and the probability of one beating another in a matchup is determined by the difference between their scores. Elo is the engineering implementation of this model in online-update form.

Chatbot Arena uses anonymous random matchups—users blindly choose the better response without knowing the model's identity, and rankings are derived from millions of votes. The advantage is that no "absolute standard" needs defining; all that is required is human judgment on "which is better, A or B." The limitation: rankings depend on what users happen to ask. If a flood of users ask programming questions, models strong at programming rank higher—which may say little about their level on other tasks.

When pairwise judging is performed by an LLM rather than human voting, one must also guard against **Position Bias**—the judging model systematically favors the candidate appearing in a certain position (usually the first), and the judgment may remain unchanged even if the content of the two candidates is completely swapped. The standard mitigation method is to **evaluate each pair twice with swapped order**: once with A first, once with B first, and average the two results; a stricter approach is to only count cases where the two judgments are consistent, and treat inconsistencies as ties or send them for human review. Chatbot Arena's approach is essentially the same—randomizing the display positions of the two responses so that position bias cancels out over a large sample.

> **Experiment 7-8 ★★: Building a Model Leaderboard from Pairwise Comparison Data**
>
> This experiment aims to deeply understand how the Bradley-Terry model extracts relative ability scores from a large number of pairwise comparisons by implementing an Elo rating calculation system from scratch. Use the real open-source voting dataset from Chatbot Arena (containing millions of anonymous user blind votes).
>
> Implement the Elo rating iterative update algorithm: Initialize all models with a rating of 1000. Process voting records in chronological order. For each matchup, calculate the expected win rate based on the current rating difference between the two models, compare the actual result with the expectation, and adjust ratings by a fixed learning rate—the winner gains points, the loser loses points, with the adjustment magnitude proportional to the deviation from the expectation (an upset loss results in a larger rating change). Sort models in descending order by final rating and calculate the pairwise win rate matrix. Compare with the official leaderboard to verify that the rankings are generally consistent. Exact point-for-point alignment is not required: the official Chatbot Arena uses Bradley-Terry maximum likelihood estimation (solving all matchups simultaneously, independent of voting order), while this implementation uses online incremental Elo updates (results are affected by the learning rate K-factor and processing order). The two algorithms should yield consistent overall rankings, but the specific scores will not be precisely identical.
>
> The second part of the experiment creates a historical ranking evolution animation: Slice the voting data by time (weekly or monthly) and calculate Elo rating snapshots for each time point. Use D3.js to implement a bar chart race animation (horizontal bar length = rating, vertical position = ranking, smoothly changing over time). By observing the animation, identify technology breakthrough moments (a model's rating suddenly surges), competitive landscape evolution, and model lifecycles.
>

## Evaluation-Driven Model Selection

Model selection is not simply about "choosing the strongest model"; it involves making evaluation-driven trade-offs across multiple dimensions based on the application scenario.

### Key Dimensions for Selection

**Throughput** and **Latency** are two families of metrics that are easily confused; untangling them takes only one fact—LLM inference runs in two stages. **Prefill** reads the entire context at once and determines the **Time To First Token (TTFT)**: the delay between the user pressing Enter and the first character appearing. The longer the context, the slower the prefill and the higher the TTFT. **Decode** then generates the response token by token, setting the generation speed (tokens/second)—which also dictates thinking time: at 50 tokens/s, a model producing 2000 thinking tokens spends 40 seconds just thinking.

Around these two stages, the main throughput and latency metrics are as follows:

- **Input Throughput / Output Throughput**: Correspond to the speed of Prefill and Decode, respectively.
- **TTFT**: Equals queuing time plus Prefill time; it is the user-perceived "responsiveness."
- **Thinking Latency**: The number of thinking tokens generated can vary severalfold across models, and thinking length is not necessarily positively correlated with task effectiveness—measure each model's thinking token usage and the corresponding benefit on your own workload, rather than inferring from public leaderboards alone.
- **p95 Tail Latency**: The latency that 95% of requests will not exceed. It is a better indicator of real user experience than the average, which can be pulled down by a large number of fast requests, masking severe slowdowns experienced by a minority of users.

**Cost**: Pricing for input/output/cache tokens. Cost should not be evaluated in isolation—a cheap model with a low success rate may actually incur higher costs due to frequent retries. The average cost per task and the cost-performance ratio need to be calculated.

**Performance**: The precise definitions of Pass@1, Pass^k, Pass@k, and Best@k are given earlier in the "Evaluation Metrics System." Here, we only discuss how to choose in the context of model selection—for daily scenarios, focus on Pass@1 (single-attempt average success rate); for critical operations, prioritize Pass^k, focusing on the stability of "never making a mistake"; for exploratory tasks, prioritize Pass@k or Best@k, looking at the upper bound of capability given enough opportunities; for open-ended tasks, use multi-dimensional Rubric scoring.

**Rate Limits and Reliability**: RPM (Requests Per Minute) / TPM (Tokens Per Minute) limits affect concurrency capabilities, and some APIs dynamically adjust quotas during peak hours. In terms of robustness, pay attention to out-of-distribution data, adversarial inputs, and long-running stability (whether issues like mode collapse or attention drift occur).

**Budget–capability curves**: A single score at a fixed budget is not enough to determine whether an Agent can handle long-horizon work. In addition to success rate, report how performance changes with wall-clock time, tokens, tool calls, or compute budget. RE-Bench makes the problem concrete: with a total budget of two hours per environment, the best Agent scored about four times as high as human experts; humans, however, benefited more from additional time, narrowly surpassed the best Agent at eight hours, and scored about twice as high when multiple attempts were given 32 total hours[^re-bench-2025]. Short-budget leadership therefore cannot be extrapolated directly to long-running capability. Model selection should compare several budget points close to the duration of the real workload.

In practice you can mix models: lightweight models on simple requests to cut costs, powerful models on complex tasks to protect quality; or specialist models on particular sub-tasks (image understanding, code generation), collaborating through sub-agent mechanisms. Any such heterogeneous combination must itself be validated by evaluation, to confirm the overall benefit outweighs the added system complexity (for example, treating questions like "which is larger, 9.9 or 9.11?" or "I want to wash the car; the car wash is 50 meters from home—should I walk or drive?" as simple ones and handing them to a lightweight model, leading to wrong decisions).

### Model Behavior: When to Stop Reading and Start Editing

Model selection compares not only whether a model can finish a task, but also **how it behaves by default**. One readily observable difference in Coding Agents is the action threshold. Given the same coding task, some models explore the repository broadly and confirm the architecture, callers, and tests before editing. Others localize from less evidence, edit early, and use test feedback to complete their understanding. The former assigns a higher cost to premature edits; the latter assigns a higher opportunity cost to reading one more file.

This tendency in an Agent has two sources: the system prompt in the harness, and the model's behavioral policy. Post-training is a key source of that behavioral policy: SFT trajectories demonstrate "how much to read before acting," process rewards reward or penalize particular tool paths, and outcome rewards reinforce the entire policy that ended in success. Over time, what the model learns is not only how to write code, but also engineering habits.

> **Experiment 7-9 ★★: Measuring Model Action Thresholds in a Fixed Coding Harness**
>
> **Objective**: Isolate the model factor, quantify how Coding models trade off continued information gathering against starting to edit, and evaluate path efficiency together with outcome quality.
>
> **Method**: Run `chapter6/model-action-threshold/experiment.py`. By default it calls GPT-5.6-sol and Claude Sonnet 5 through the same OpenRouter OpenAI-compatible endpoint while fixing the system prompt, tool schemas, task repositories, test commands, and turn limit. The neutral prompt specifies neither a minimum number of files to read nor a requirement to edit quickly. Repeat each of the three task categories at least three times and alternate model order. Record tool calls, files read, searches, and wall-clock time before the first edit, along with first-tested-patch acceptance, post-test rework, final success, changed files, and token usage.
>
> **Causal interpretation**: The neutral campaign asks whether behavior changes with the model inside one harness. To measure the harness as a modifier, run a separate campaign with `--policy explore-first`; do not mix the two policies in one model comparison. Behavior that changes with a model swap and persists for the same model across harnesses is stronger evidence of a model effect; the reverse is stronger evidence of a harness effect.
>
> **Acceptance criteria**: All offline unit tests pass; every task fixture is first confirmed to fail its tests; the formal result contains every `model × task × trial` cell, zero API errors, an independent final test, and auditable trajectories; and `manifest.json` verifies the hashes of the configuration, observations, and summary. The project directory includes one complete 18/18-cell run. Readers should rerun it on the model versions and real workloads they care about rather than treating these miniature-repository numbers as a permanent leaderboard.

### Cost Analysis of Agent Systems

The previous section listed cost among the key selection dimensions, but Agent costs are far more complex than simple token pricing—multi-turn reasoning, tool calls, and context accumulation make costs grow non-linearly. Systematic cost analysis is an indispensable part of the evaluation system and a prerequisite for production deployment.

**Components of Cost.**

The cost of an Agent system can be decomposed into three levels:

**Model inference cost** is the most direct component, determined by the consumption of input tokens and output tokens. However, in Agent scenarios, there are two often-overlooked amplifying factors. The first is the **context accumulation effect**: each time an Agent calls an LLM, it sends all previous conversation history and tool outputs together (so the model can understand the context). Without effectively utilizing KV Cache (i.e., caching already processed context to avoid redundant computation), the cost grows very quickly—Round 1 sends 1000 tokens, Round 2 sends 2000 tokens, Round 3 sends 3000 tokens, totaling 1000+2000+3000=6000 instead of 3×1000=3000. The more rounds, the larger the gap. The second is **thinking token cost**: models that support thinking generate a large number of thinking tokens. Although these tokens are not displayed to the user, they are still billed.

**Tool call cost** includes external API fees (search engines charge per query, database queries consume computing resources), sandbox resources for code execution, and an easily overlooked indirect cost: the token cost incurred when tool outputs are injected into the context. The content returned from a single web search might occupy 2000-5000 tokens, and it will be repeatedly billed as input in every subsequent round of inference.

**Infrastructure cost** covers operational overhead for vector databases (used for RAG retrieval), message queues, relational databases, and logging and tracing storage (for observability).

To see where these costs actually come from, the companion experiment used a fixed eight-turn refund workflow: query the order, logistics, refund policy, and knowledge base, then perform risk checks, issue the refund, notify the user, and close the case. Real gpt-4o-mini calls were run under all four combinations of two switches: stable versus unstable prefixes, and full versus compressed history. The business workflow was identical in every arm. Table 7-4 uses the recorded token counts and prices from that run.

Table 7-4 Measured Cost of the Eight-Turn Agent Workflow

| Configuration | Input Tokens | Cached Tokens | Total Cost | Savings vs. Baseline |
|---|---:|---:|---:|---:|
| No cache, no compression | 20,700 | 0 | $0.003776 | — |
| Stable prefix only | 20,386 | 13,568 | $0.002707 | 28.3% |
| History compression only | 16,177 | 0 | $0.003115 | 17.5% |
| Stable prefix + compression | 16,035 | 6,144 | $0.002643 | 30.0% |

In the baseline, input grew from 1,113 tokens on the first turn to 3,668 on the last. Tool results were repeatedly carried into later requests, accounting for 9,544 input tokens across the run. With both optimizations enabled, that figure fell to 5,248 and total cost dropped by 30%.

The gains were not additive. A stable prefix alone saved 28.3%, and compression alone saved 17.5%, yet together they saved 30%, not 45.8%. Compressing history also shortened the prefix available for cache reuse. **When context optimizations are combined, measure the complete workflow; never add their isolated savings together.** A different model, price schedule, or task length will change the 30% figure. The reusable result is the four-arm method, not the percentage itself.

**Cost Optimization Strategies.**

The first input-side levers to test are **KV Cache Reuse** (keep the prefix stable), **Context Compression** (shorten old trajectories and verbose tool results), and **Tiered Model Routing** (send simple requests to lightweight models and difficult reasoning to stronger ones). Chapter 2 covered the implementations. Here the operational point is that each lever should have its own switch, so the team can measure both its isolated effect and what happens when it is combined with others. Two further methods matter specifically to evaluation and operations.

**Asynchronous Batch Processing** accumulates non-real-time tasks for batch processing, leveraging batch pricing discounts from API providers; in self-deployment scenarios, it also improves GPU utilization during off-peak hours.

**Cost Monitoring and Budget Control.**

In a production environment, a real-time cost monitoring system should be established: track token consumption and API costs by task type, model, user, etc. Also, set a cost cap for each task—automatically terminate the Agent when it falls into a loop or explores too deeply, preventing a single task from incurring abnormally high costs.

> **Experiment 7-10 ★: End-to-End Cost Analysis of Agent Tasks**
>
> **Experiment Goal**: Reproduce the eight-turn cost breakdown above, then test the same optimization levers on your own workload.
>
> **Technical Approach**: Reproduce the fixed companion task first, then select several representative tasks of your own. Use LangSmith or a self-built tracing system to record input/output and thinking tokens, tool-call counts and return sizes, and end-to-end latency for every LLM call. Calculate average cost, p50/p95/p99, and the cost breakdown for each task type.
>
> **Acceptance Criteria**: Generate a cost report and identify the main drivers. Run all four switch combinations, measuring each optimization alone and both together. Rerun the experiment after changing models rather than carrying forward the saved trace's percentage savings.
>
>

### Evaluation-Driven Continuous Iteration

Model selection is not a one-time decision but a continuous process, adjusted as models evolve. The chapter opened with the claim that an evaluation system lets you keep pace with model evolution; a concrete model-switching case shows how that plays out in a real decision.

Suppose your Agent system is currently built on Claude, excelling in tool calling and complex orchestration. One day, Gemini releases a new model, and public benchmarks show it surpasses Claude on several metrics at a lower price. At this point, your question is not "Is Gemini better than Claude?" but "**On my specific tasks, is Gemini better than Claude? How much better? What is the switching cost?**"

A team with a solid evaluation system can answer this in hours: run the new model on its own evaluation dataset and compare task success rate, tool call accuracy, latency, and cost. You might find the new model really is better and cheaper on simple tasks—but in the core scenarios involving complex multi-round tool orchestration, its success rate drops by 5%. Once you confirm the difference exceeds the estimated sampling noise (see "Statistical Significance of Evaluation Results" below), your decision becomes a differentiated strategy—migrate simple tasks to the new model to cut costs, keep the original model on complex tasks to protect quality—rather than a blind wholesale switch. Decisions this granular and data-driven are only possible with an evaluation system built in advance.

> **Experiment 7-11 ★★: Multi-Dimensional Model Performance Benchmarking**
>
> Conduct a comprehensive benchmark of mainstream LLMs and different API providers to build a multi-dimensional model selection decision database.
>
> Select test scope: Closed-source SOTA models like GPT series, Claude series, Gemini series, Doubao series, and open-source models like Qwen, Kimi, DeepSeek. Test the same model with different API providers (e.g., DeepSeek official vs. Siliconflow) to verify results from third-party performance monitoring platforms (e.g., Artificial Analysis).
>
> Design standardized test workloads: Input throughput tests use fixed-length contexts (8K/32K/128K tokens), output throughput tests request fixed-length responses (512/2048 tokens). Latency tests include TTFT (Time to First Token) and end-to-end latency. For models supporting thinking, separately measure thinking length and thinking latency. For each configuration, make at least 100 requests and calculate the standard deviation, p50, p95, and p99; high latency variance indicates an unstable user experience.
>
> Evaluate API availability and stability: Probe once per hour for a week, recording success rate, error types, and failure duration. Calculate failure rate, MTTR (Mean Time to Recovery), and longest continuous uptime. Test the actual thresholds of rate limits—gradually increase concurrency to find the throttling point, recording RPM/TPM limits. Calculate comprehensive cost: Collect pricing information (unit prices for input/output/cache tokens), consider the impact of KV Cache, and calculate the average cost for typical multi-round Agent tasks.
>
> **Experiment 7-12 ★★: End-to-End Selection Evaluation of User Memory Systems**
>
> **Prerequisites**: Must complete the contextual retrieval or agentic RAG experiment from Chapter 3.
>
> **Goal**: Perform an end-to-end model-selection evaluation of a user-memory retrieval Agent, examining how the embedding model, reranker, and Agent's main model jointly affect retrieval quality, latency, and cost. Reuse `chapter3/contextual-retrieval-for-user-memory` or `chapter3/agentic-rag-for-user-memory`, and compare the configurations on 60 test cases.
>
> **Acceptance**: Evaluate each of the three selection points in turn—embedding model (BGE-M3 / OpenAI / Doubao, etc., record top-5 retrieval accuracy, latency, cost), reranker (include a "no reranker" baseline, quantify its marginal value), and main model (compare success rate and tool usage efficiency under the same retrieval configuration). The key is to identify synergies among the components: a stronger embedding might make the reranker redundant, and a stronger main model might compensate for retrieval shortcomings. Selection is a systemic trade-off, not simply a matter of choosing the strongest component in isolation. Configuration details are in the companion repository.
>

## Statistical Significance of Evaluation Results

The evaluation set is finite and model outputs are stochastic, so a score difference may be nothing but sampling noise. If you measure a success rate $p$ over $n$ cases, the standard error can be roughly estimated as:

$$
\mathrm{SE}(p)\approx\sqrt{\frac{p(1-p)}{n}}
$$

For example, with 100 cases and a 70% success rate, the 95% confidence interval is about $70\%\pm9$ percentage points; "the new model gets 73% versus the old model's 70%" is not enough to justify switching.

When comparing two configurations on the same batch of tasks, prefer **paired analysis**: record per task which one wins, and judge the difference with McNemar's test or a paired bootstrap, rather than subtracting two independent success rates. Because each Agent run may also differ, it is best to run each configuration with several random seeds (say 3–5) and report the mean along with the spread; a single run is only good for screening a direction. If the expected gain is only 2–3 percentage points and the evaluation set has only a few dozen tasks, enlarge the sample first—the standard error shrinks as $1/\sqrt{n}$.

```python
for task in paired_tasks:
    for seed in fixed_seeds:
        a = run(config_a, task, seed)
        b = run(config_b, task, seed)
        record_paired_delta(verifier(a), verifier(b))

return paired_bootstrap_or_mcnemar(all_deltas)
```

Pairing means that both groups share the same tasks and random conditions, not that you draw two separate samples and compare their averages.

When validating several hypotheses in parallel, also account for **multiple comparisons**: tighten the significance threshold, or re-run positive results independently. The practical criterion is simple: a score gap is worth acting on—switching models or shipping a change—only if it exceeds the noise, holds up under paired analysis, and can be reproduced.

## Agent Observability

Evaluation-driven decisions (whether for model selection or continuous iteration) rely on high-quality operational data. Below, we first introduce how to systematically collect this data (observability), and then discuss how to translate evaluation results into system improvements.

![Figure 7-7: Observability Technology Stack](images/fig7-7.svg)

Observability is a concept borrowed from distributed systems: you cannot open the system and watch it work; you infer what is happening from the logs, metrics, and traces it emits—the way a doctor, unable to see inside a patient, diagnoses from temperature, blood pressure, and imaging. Agent systems make this harder still: the same input can produce different outputs, multi-round reasoning and tool calls make execution paths extremely complex, and the model's "thinking" is completely opaque from outside.

The value of observability lies first in **problem diagnosis**: complete traces allow developers to replay the entire process rather than guessing. Second, it is the foundation for **continuous optimization**—you can see which tasks require multiple rounds of iteration, which tools have the lowest success rate, and which retrieval queries always return empty results. In **cost management**, Agent operating costs can differ by one or two orders of magnitude between tasks, and tracing surfaces the abnormally expensive cases. Finally, accumulated trace data underpins later system optimization and model improvement.

Agent observability is built on the foundation of **traces**, whose data structure directly inherits the span tree model from distributed systems: one task execution corresponds to one trace, where each LLM call, each tool call, and each retrieval is a **span** (an execution unit recording input/output, start/end times, token consumption, and error information). The parent-child relationships between spans form an execution tree—for example, an "Agent Main Loop" span may have several "LLM Call" and "Tool Call" child spans hanging beneath it. Standardized protocols are already available for this layer: **OpenTelemetry** is the general-purpose distributed tracing standard, while specifications like **OpenInference** define LLM-specific semantic conventions on top of it (how to record prompts, model parameters, token usage, etc.). The advantage of adopting standard protocols is the decoupling of collection and analysis—the same trace data can be connected to different analysis backends, avoiding vendor lock-in.

LangSmith is one of the representative platforms in this domain (similar platforms include Langfuse, Arize Phoenix, etc.), integrating observability, evaluation, and optimization into a closed loop. Each execution creates a trace session, where model calls, tool usage, and knowledge retrieval are recorded as independent execution units, linked by causal relationships to form an execution tree. Each unit records complete input/output, timing information, cost data, and error information. The platform uses asynchronous batch data collection to ensure that tracing itself does not affect the Agent's response latency.

The platform also supports A/B testing (routing a portion of user traffic to a new version, automatically comparing metrics, and supporting rapid rollback or gradual scaling), prompt version management (each version is associated with runtime performance data), and collaborative development (team members can share trace data and problem cases). The massive amount of real-world data from production environments is a goldmine for continuous improvement—it can uncover unforeseen scenarios and identify the features most in need of optimization.

The most valuable use of observability data is to **turn it into evaluation assets**. A practical loop: extract failed and suspicious cases from production traces → anonymize them (strip sensitive fields such as user data and keys) → distill them into new test cases and regression tests for the evaluation set. The evaluation set then stops being a one-time, static collection and becomes a living asset that evolves with the product and continues to reflect the real user distribution—the failure patterns exposed in production today become the regression tests guarding the baseline tomorrow. This is precisely the interface between observability and the main theme of this chapter: observability is responsible for "seeing" what happens in the real world, and evaluation is responsible for solidifying those observations into repeatable standards.

With a comprehensive evaluation system and dataset in place, the key is to translate evaluation results into tangible system improvements.

## From Benchmark Reports to System Improvements

The following case comes from a real, deliberately narrow AndroidWorld iteration in the companion repository. It covers four Wi-Fi settings tasks on an API 35 emulator, with one matched run per task. It is not the full 116-task benchmark and does not replace a rerun in the reference API 33 environment. Its value is not an overall score; it is the sequence of decisions from one result to the next.

![Figure 7-8: Benchmark to Improvement Loop](images/fig7-8.svg)

From the perspective of Harness engineering, this section is essentially about the methodology for iterative Harness optimization—using evaluation data to identify weak points in the Harness (insufficient context? missing constraints? inadequate validation? untimely feedback?), making targeted improvements, and then re-evaluating, forming a closed loop for the Harness's continuous evolution.

Before analyzing any benchmark report, note an easily overlooked principle: **when Agent performance drops, check the evaluation system first, then the Agent**. The common mistake is to start editing Agent code the moment a score falls, ignoring the possibility that the evaluation system broke first—steer by a distorted signal and the correction is wrong from the very first step. Typical evaluation-side failures include: the runtime environment running out of resources and killing processes (which shows up as random failures), bugs in the verifier that mark correct answers as failures, and test cases drifting out of sync with production scenarios. In the headline numbers, all of these look identical to model degradation; only a review of the full traces can tell them apart.

### Reading a Benchmark Report: The Art of Problem Discovery

The starting report recorded one run on each of 116 tasks and about 88% overall success. The failures were not scattered: three of the four `SystemWifiTurn*` tasks failed, and their traces repeatedly navigated back and forth without confirming the final state. Two explanations fit the evidence: the Agent did not know where to go, or the UI representation it received was incomplete.

An 88% headline score hides this small but coherent failure cluster. Raising the step limit would be equally misleading—it could recast "the Agent cannot see the control" as "the Agent needs more persistence." Read reports in the opposite direction: locate clusters by task and capability tag, replay the traces, decide whether the failure arose in observation, reasoning, action, or verification, and only then choose a variable to change. The Wi-Fi slice was used to diagnose the mechanism cheaply, not to estimate system-wide performance.

### From Data to Hypotheses: Building an Improvement Roadmap

The first round tested the cheapest explanation. H1 assumed a navigation-knowledge gap, so only the treatment received Wi-Fi navigation and final-state-checking instructions. Success did not improve; the prompt was not the bottleneck.

The second round asked what the Agent could actually see. H5 replaced the API-35-incompatible accessibility feed with AndroidWorld's supported UIAutomator tree. Success improved, but the full tree caused token use to surge. H5C therefore added no new information: it simply removed invisible, textless, non-actionable container nodes to see whether the same success could be preserved with less noise.

Across all three rounds, the model, task parameters, seed, step limit, and emulator stayed fixed, and arm order alternated. This staged design made attribution straightforward: the residual problem or side effect from one round became the sole change in the next.

### From Results to Decisions: Data-Driven Trade-offs

Table 7-5 summarizes the measured results. With only four tasks per arm, these numbers can decide whether a larger rerun is worthwhile; they cannot estimate success across AndroidWorld.

Table 7-5 Three Rounds on the AndroidWorld Wi-Fi Slice

| Experiment | Only Change | Control → Treatment Success | Treatment / Control Tokens | Next Step |
|---|---|---:|---:|---|
| H1 | Add navigation instructions | 25% → 25% | 0.47× | No success gain; retain the original prompt |
| H5 | Accessibility feed → UIAutomator | 25% → 100% | 2.498× | Strong gain but too expensive; continue optimizing |
| H5C | Compact the UIAutomator tree | 100% → 100% | 0.506× | Preserve success and halve tokens; advance to a full rerun |

The sequence matters more than any one percentage. More detailed instructions cannot restore information the Agent never received; observation failures should be investigated before prompts are expanded. But more input is not always better either. The full element tree fixed visibility while flooding the context with noise. Removing non-semantic nodes preserved four successful runs and cut tokens by roughly half. No model was changed: the Harness's UI representation first determined whether the task could be completed and then whether completing it was economical.

### Continuous Iteration: From First Improvement to System Evolution

Passing H5C on four tasks only earns it a larger test; it does not authorize deployment. The next gate is a five-seed run over all 116 tasks in the Pixel 6 / API 33 reference environment with the full third-party app set. Success must be non-inferior, token use no more than 75% of the original, and latency no more than 1.5×. Until that run is complete, 4/4 on the slice must not be reported as 100% system-wide success.

That is what continuous iteration means in practice: evidence from one round should authorize only the next action that its scope can support. H1 stopped further prompt piling; H5 found the right mechanism and revealed a cost problem; H5C fixed that problem and qualified for broader testing. A good benchmark report contains more than a score. It states where the conclusion applies, which guardrails failed, and what must be tested next.

> **Experiment 7-13 ★★★: Evaluation and Improvement on AndroidWorld**
>
> This experiment practices the full path from evaluation report to system improvement. Start with the historical report and three saved paired runs in `chapter6/android-world`.
>
> Step 1: Diagnosis. Cross-analyze the per-task table and the capability tag matrix to map surface-level task failures to deep-seated capability deficiencies. Identify capability tags with lower-than-expected success rates and task areas with concentrated failures.
>
> Step 2: Build Hypotheses. Formulate improvement hypotheses following the three-layer framework (surface → mid → deep). Each hypothesis should state the target improvement in success rate and the verification method.
>
> Step 3: Phased Experimentation. Reproduce H1, H5, and H5C with one variable changed per round. Record tokens, latency, and regressions as well as success.
>
> Step 4: Data-Driven Decision Making. Make deployment decisions based on cost-benefit analysis—not simply adopting all effective improvements, but weighing the scope of application, latency impact, and cost overhead for each improvement. Prioritize low-cost, high-benefit improvements for deployment; restrict high-cost improvements to critical scenarios.
>
> Step 5: Iteration. A passing slice experiment advances only to the full rerun. Discuss deployment only after the 116×5 reference-environment run, and preserve environment differences, sample size, and incomplete scope in the report.
>

## From External Evaluation to Internal Evaluation: Evaluation Infrastructure for Production-Grade Agents

So far this chapter has evaluated Agent systems from the outside—building an evaluation environment, designing datasets, analyzing benchmark reports. But the best Agent products do more than undergo external evaluation; they **build continuous self-evaluation infrastructure into the product**. Below, using the open-source general-purpose Agent OpenClaw introduced in Chapter 5 as an example and drawing on public technical analyses of leading Coding Agent products and practitioner insights, we present an internal evaluation system worth emulating: one that systematically embeds the experimental methodology of ML research into product engineering.

### Ablation Infrastructure: Understanding the True Contribution of Each Feature

ML researchers have long used ablation studies to learn which components of a model actually matter—ablation means "removing" one component at a time and observing how much overall performance drops. OpenClaw brings this methodology into product engineering: a built-in master switch can disable several major features at once (thinking mode, context compression, automatic memory, background tasks, and more), creating a "bare model" baseline. That lets the team answer a key question: **does a feature truly improve the user experience, or does it just feel useful?**

Making ablation a routine engineering practice, rather than a one-time research activity, has several practical implications. First, the ablation switch must be injected very early in the startup path—before any module-level constant captures configuration values—meaning the ablation infrastructure must be designed into the system architecture from the start, not retrofitted later. Second, running ablation experiments regularly (e.g., before each major release) can uncover "feature debt"—features that were once effective but are no longer necessary as models evolve. For any team building a production Agent, the recommended practice is: **Every major feature should be independently disableable, and the team should regularly verify the actual contribution of each feature.**

### A/B Testing Methodology: Distinguishing Mechanism from Goal

Mature Agent products conduct rigorous A/B testing on their own behavior (i.e., randomly dividing users into two groups, one using the old version and one using the new version, and comparing actual data from both groups to determine if a change is effective). A well-designed Agent A/B test case illustrates several key methodological principles:

**Multiple variants, not just a binary comparison.** Instead of just comparing "with" and "without," design multiple progressive variants (e.g., when testing different strengths of prompt constraints, set up a control group and three experimental groups with progressively stricter constraints). This design can reveal dose-response relationships and help find the optimal point.

**Distinguishing mechanism metrics from target metrics.** This is the easiest mistake to make—treating what you are changing as the optimization target. For example, if you are testing "shortening the Agent's plan file length," plan length is a mechanism metric (something you directly change), but it is not the target. The real target might be "reducing session-level cost." Shortening the plan file may lower costs, but it could also lead to more edit-check-edit loops due to insufficiently detailed plans, increasing total output. Always ask yourself: **Is what I am changing (the mechanism) the same as what I truly care about (the target)?** If not, prioritize the target.

**Setting guardrail metrics.** Even if the target metric improves, the experiment should be stopped if user satisfaction declines, the number of operations increases, or the error rate rises. Guardrail metrics are non-negotiable thresholds that must not regress.

**Recording baseline statistics.** Include sample size, distribution percentiles, and correlation analysis (e.g., "rejection rate increases monotonically with plan size") to provide the necessary context for interpreting experimental results. Without a baseline, you cannot determine whether the experimental results are statistically significant.

### Two-Layer Feature Flag System

Agent products need a Feature Flag infrastructure designed from day one—a feature flag is a remotely controllable switch that determines whether a function is enabled or disabled for users, without requiring code redeployment. It serves three purposes simultaneously: experimentation, gradual rollout, and emergency circuit breaking.

**Compile-time flags** physically remove the relevant code from the build artifact during the build phase. Internal-only features simply do not exist in external builds—even reverse engineering cannot discover the removed functionality. This also provides a clean ablation mechanism: disabling a feature does not skip logic at runtime; the corresponding code is physically absent.

**Runtime flags** have their configuration delivered by the server and cached locally on disk. The design prioritizes reading slightly stale cached configuration over blocking the Agent's startup while waiting for a network request. Specific grouping decisions are made through an experimentation platform (e.g., GrowthBook) for assigning A/B test groups. A key design detail is that each feature's exposure event is logged at most once per session to avoid duplicate records polluting the experimental data.

The lesson for Agent developers: feature flags are not debugging tools; they are **first-class architectural components**.

### Prompt Sensitivity Assessment

The system prompt is the core "code" of Agent behavior, yet it often lacks the version control and regression testing afforded to regular code. OpenClaw's approach is to provide a dedicated tool that can extract the fully rendered system prompt at a specified Git revision or commit—including the final text after all dynamic conditions are expanded. This allows the team to precisely answer: **Which commit changed the prompt? What was the impact on the evaluation set?**

For any Agent team, the recommended practices are: (1) The system prompt should be deterministically renderable (given the same configuration input, it always produces the same output); (2) Establish a versioned snapshot mechanism for prompts; (3) Every prompt change should run regression tests on the evaluation set—just as code changes require CI.

### Privacy-Aware Analytics as an Evaluation Foundation

Evaluation relies on good data, but Agent products often handle sensitive user content. OpenClaw resolves this contradiction through a type system: the analytics interface only accepts values wrapped in special types, where the type name itself serves as an audit trail—it explicitly declares "I have verified this is not code or a file path." This design transforms privacy constraints from documented specifications into compile-time enforced type checks.

The core principle is: **Design privacy constraints into the system from the start; do not bolt them on afterward.** If your analytics system cannot safely collect data, you cannot evaluate effectively. Privacy and evaluation are not opposing forces—privacy-aware design forces you to think carefully about *what truly needs to be measured*, which in turn fosters more precise evaluation metrics.

### From External to Internal: A Shift in Evaluation Thinking

The core message of this section is: **The previous sections taught you how to evaluate an Agent externally; this section reveals how the best Agent products evaluate themselves internally.** External evaluation tells you "how good the Agent is"; internal evaluation infrastructure tells you "which change made it better." Ablation experiments discover which features truly matter, A/B testing quantifies the impact of each change, feature flags provide the infrastructure for experimentation and rollback, prompt sensitivity assessment integrates the system prompt into the CI system, and privacy-aware analytics ensures compliance in data collection. These five components together constitute evaluation-driven product engineering—not evaluating occasionally, but embedding evaluation into every product decision.

## Simulation Environments: The Bridge from Evaluation to Post-Training

The endpoint of evaluation is not scoring, but improvement. This chapter has already demonstrated two paths for improvement: adjusting the Harness (from Benchmark reports to system improvements) and embedding evaluation into product engineering (internal evaluation infrastructure). The strongest form of improvement is training—when the goal expands from "evaluating existing capabilities" to "cultivating new capabilities," especially through the post-training techniques discussed in Chapter 8, the evaluation environment needs to evolve into a **simulation environment**: a virtual playground where the Agent can repeatedly practice and be automatically scored. The core differences between simulation environments and evaluation environments are: much higher interaction frequency (millions vs. thousands), the need for randomization (to prevent memorizing specific configurations), and the requirement for immediate feedback. From an application perspective, simulation environments are divided into two categories: digital environments (information processing tasks) and embodied environments (physical world perception and manipulation).

Here is how the two ends of the bridge meet. Assets accumulated on the evaluation side convert almost seamlessly into training signals: a well-defined Rubric or validator is essentially a reward function for **Reinforcement Learning with Verifiable Rewards (RLVR)**—the scoring script becomes the reward script; whether a test passes or a state meets the standard serves both as an evaluation criterion and as a reinforcement learning reward. But training brings demands evaluation never had to worry about. The first is **reliable reset semantics**: training runs millions of episodes (an episode is one complete interaction round from an initial state to task completion), and each episode must be able to reset the environment to a deterministic, clean initial state; otherwise, the gradient signal will be contaminated by residual states from the previous episode. The second is **throughput far exceeding evaluation**: a few thousand evaluations are enough to draw conclusions, but training requires feeding the model millions of interactions within an acceptable wall-clock time; the degree of environment parallelism and per-instance overhead directly determine whether training is feasible. These two points—validators turned into reward functions, and training-grade reset and throughput—will be elaborated in Chapter 8.

![Figure 7-9: Simulation Fidelity Spectrum](images/fig7-9.svg)

On the **digital environment** side, the AWorld framework builds a controllable MCP server sandbox for GAIA tasks, providing 26 MCP servers covering 126 tool functions, avoiding the bans and uncontrollable side effects of directly accessing real APIs. All tool calls are replayable and auditable. AWorld's distributed architecture reduces the traditional serial execution time from 7695 seconds to 525 seconds (a 14.6x speedup), and the environment's stateless design makes each instance completely independent, supporting efficient parallelism.

On the **embodied environment** side, RoboTwin2 builds dual-arm manipulation tasks based on a physics engine, randomizing object positions, orientations, and appearances to improve generalization. The observation space includes multi-camera visuals and joint states, achieving real-time control through **Action Chunking**—where the model plans multiple consecutive actions at once (detailed in Chapter 6). OSWorld provides reset capability through virtual machine snapshots, and AndroidWorld focuses on mobile application automation. Whether digital or embodied, simulation environments also require the isolated execution environments and virtual identity mechanisms discussed in Chapter 4 (VM/container isolation, residential proxies, Human-in-the-Loop authentication, shared file systems), which will not be repeated here.

> **Experiment 7-14 ★★: Configure the Embodied Intelligence Environment for OpenVLA and RoboTwin2**
>
> Set up a simulation environment for robot manipulation. Read `ch7/SimpleVLA-RL` and the OpenVLA documentation to understand the architecture of the Vision-Language-Action model (end-to-end integration of a vision encoder, language model, and action decoder, projecting images and text into a shared semantic space). Configure the RoboTwin2 environment, understanding the observation space (three-view RGB + 14-dimensional joint state) and action space (14-dimensional control vector). Study the environment randomization mechanism and spatial constraint logic in `move_can_pot`. Evaluate the pretrained model, recording its success rate, completion time, and failure modes, with a focus on the impact of the action chunking mechanism.
>
>
> ![Figure 7-10: OpenVLA and RoboTwin2 Embodied Intelligence Environment](images/fig7-10.svg)
>
>

### Fidelity Trade-offs and Domain Randomization

High-fidelity environments support better transfer to the real world but have high computational costs. Another dimension of fidelity is the degree of randomization: moderate randomization improves generalization, while excessive randomization can make tasks too difficult. **Domain Randomization** is a key technique for narrowing the sim-to-real gap: introducing a wide range of random variations in physical parameters, visual appearance, sensor noise, etc.—just like practicing grasping under various lighting and angles, so you won't fail in the real world just because the light changes. In digital environments, sim-to-real manifests as differences in interface rendering, response times, etc., which can be mitigated by introducing randomization in latency and failures.

[^re-bench-2025]: Wijk, Hjalmar, et al. *RE-Bench: Evaluating Frontier AI R&D Capabilities of Language Model Agents against Human Experts.* arXiv:2411.15114, 2025.

## Chapter Summary

This chapter has revolved around one core question: how do you tell whether an Agent has gotten better or worse? The chain has four stages — first pin down what counts as success (the differing bases of Pass@k, Best@k, and Pass consecutive@k), then settle where the tasks come from (public benchmarks, a self-built business set, and production trajectory feedback), then choose how verification is done (from deterministic verifiers to checklists, Rubric plus LLM judgment, and finally pairwise comparison), and finally turn scores into decisions (statistical significance, failure attribution, regression tasks, and model selection). Every stage affects how much you can trust the conclusion.

In terms of the book's larger structure, this chapter builds the **evidence** segment of Chapter 1's discovery loop: failure attribution determines whether later proposals have anything solid to rest on.

Trajectory-prefix boundary evaluation makes a further point: **obtaining a piece of information and correctly applying it to the current decision are two different capabilities**. End-to-end regression guarantees that basic tasks do not degrade, while the trajectory-prefix boundary set directly checks scope judgment, current-instruction override, clarification, and confirmation before dangerous actions. User memory is just one case of this general method. Evaluation for production-grade Agents is not an occasional exam, but a verification system that continuously generates regression tasks and boundary tasks from real problem cases.

Core methodology: Observe → Hypothesize → Experiment → Validate → New Understanding → New Hypothesis, transforming Agent engineering from experience-driven "alchemy" to data-driven scientific engineering.

The evaluation system introduced in this chapter forms a complete closed loop: **Evaluation Environment** provides automated testing infrastructure → **Evaluation Dataset** defines test cases → **Automated Evaluation Methods** (deterministic verifiers, LLM-as-a-Judge, and Rubric) score Agent performance → **Benchmark Analysis** reveals improvement directions → **System Improvements** fix issues → Update the evaluation environment and dataset, starting a new iteration cycle.

The evaluation system established in this chapter serves not only the optimization of the current system but also provides a critical foundation for the next two chapters. Chapter 8 turns evaluation environments and data into inputs for model post-training; Chapter 9 turns multidimensional evaluation of production trajectories into updates to knowledge, instructions, and procedures.

## Thought Questions

1. ★★ LLM-as-a-Judge uses a language model to evaluate the output of a language model. Does this "self-evaluation" have systematic blind spots—for example, the model might consistently give high scores to a certain style of response, a preference that is inconsistent with human judgment? How can such biases be detected and corrected?
2. ★★★ The "leakage-proof" design of evaluation datasets is crucial. However, in the open-source ecosystem, once benchmark data is made public, it is quickly incorporated into training data. Does this "cat-and-mouse game" have an endgame? Design an evaluation method that fundamentally resists data leakage.
3. ★★ Scale AI's four criteria (expert guidance, comprehensive coverage, standardized importance weighting, self-contained evaluation) aim to eliminate subjectivity in evaluation. However, certain task dimensions (e.g., "Is the answer helpful?" "Is the tone appropriate?") are inherently subjective. How can reliable Rubrics be designed for these subjective dimensions?
4. ★★ τ-bench evaluates Agents by simulating real user behavior. But the simulated user itself is an LLM—it might systematically underestimate certain edge cases (e.g., emotionally agitated or unclear users). How can the quality of the simulated user itself be validated?
5. ★★ Pairwise comparison (Bradley-Terry model) assumes preferences are transitive (if A > B and B > C, then A > C). However, human preferences often violate transitivity. In Agent evaluation, in what scenarios might non-transitive preferences appear? How does this affect the reliability of rankings?
6. ★★ This chapter distinguishes Pass@k as a ceiling on capability from Pass consecutive@k as a measure of business reliability. For an Agent whose single-run success rate is only 60%, how would you combine a task's failure cost, retry cost and side effects to decide which metric to report and how large $k$ should be?
7. ★★ This chapter proposes the scientific method of "Observe → Hypothesize → Experiment → Validate." In practice, however, the Agent's behavior space is vast, and validating a single hypothesis may require hundreds of evaluation runs. How can the information gained from evaluation be maximized under a limited computational budget?
8. ★ In the AndroidWorld pilot, the full element tree raised success from 25% to 100% but increased token use to 2.498× the control; pruning preserved 100% success while reducing token use to 0.506×. How would you design automatic pruning rules that remove semantically empty UI nodes without discarding information needed for accessibility, state verification, or later actions?
9. ★★ τ-bench's user simulation employs "progressive information disclosure"—not providing all information at once, but gradually revealing it based on the Agent's questions. How does this design affect evaluation results? If the simulated user's information disclosure strategy differs significantly from real users, are the evaluation conclusions still reliable?
