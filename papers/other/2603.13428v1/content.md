# EvoClaw: Evaluating AI Agents on Continuous Software Evolution

**Authors:** Gangda Deng, Zhaoling Chen, Zhongming Yu, Haoyang Fan, Yuhong Liu, Yuxin Yang, Dhruv Parikh, Rajgopal Kannan, Le Cong, Mengdi Wang, Qian Zhang, Viktor Prasanna, Xiangru Tang, Xingyao Wang

## Abstract

Code: github.com/Hydrapse/EvoClaw Data: huggingface.co/datasets/hyd2apse/EvoClaw-data Leaderboard: evo-claw.com With AI agents increasingly deployed as long-running systems, it becomes essential to autonomously construct and continuously evolve customized software to enable interaction within dynamic environments. Yet, existing benchmarks evaluate agents on isolated, one-off coding tasks, neglecting the temporal dependencies and technical debt inherent in real-world software evolution. To bridge this gap, we introduce DeepCommit, an agentic pipeline that reconstructs verifiable Milestone DAGs from noisy commit logs, where milestones are defined as semantically cohesive development goals. These executable sequences enable EvoClaw, a novel benchmark that requires agents to sustain system integrity and limit error accumulation, dimensions of long-term software evolution largely missing from current benchmarks. Our evaluation of 12 frontier models across 4 agent frameworks reveals a critical vulnerability: overall performance scores drop significantly from >>80% on isolated tasks to at most 38% in continuous settings, exposing agents’ profound struggle with long-term maintenance and error propagation.

### Introduction

Frontier LLM-powered agents (e.g., Claude Code (Anthropic, 2025), Codex (OpenAI, 2025), and OpenHands (Wang et al., 2024)) are increasingly deployed as long-running systems into complex, open-ended environments, such as OpenClaw11https://github.com/openclaw/openclaw, where static zero-shot capabilities are intrinsically insufficient. To operate effectively in these dynamic settings, agents must treat software as a skill, which involves the autonomous development and continuous refinement of customized software interfaces. As the agent iteratively adapts to successive requirements from end-users and ongoing environmental feedback, its continuous development efforts accumulate, naturally forming a complete repository evolution history.

Yet, evaluation for such long-running agent systems remains largely under-explored.
While benchmarks for agents on coding tasks have advanced from isolated function completion to full-scale codebase generation (Table 1), they predominantly treat development as independent, one-off tasks. A critical dimension remains unaddressed: the temporal structure of software evolution. A true repository evolution benchmark must capture the full evolution itinerary—a continuous stream of dependent tasks where early implementation decisions constrain subsequent ones. Ignoring these dependencies allows agents to take expedient shortcuts that satisfy immediate tests but silently accumulate technical debt that invisible to current isolated evaluations (Yao, 2025).

To capture these long-term dynamics in a Repository Evolution benchmark, extracting realistic itineraries from open-source repositories is essential.
However, determining the appropriate task granularity is non-trivial.
Intuitively, one might attempt to measure evolution at the release-level.
However, this granularity is too coarse: release snapshots collapse the hundreds of interdependent commits between versions into a single update, flattening the fine-grained dependency structure that drives evolutionary changes.
In contrast, the commit-level history is too fine-grained: many commits are trivial (e.g., typo fixes) and the linear commit sequence encodes only chronological apply order, introducing spurious dependencies between unrelated changes.

To address this, we propose modeling software evolution at the Milestone-level.
We define a milestone as a coherent functional unit that preserves dependency constraints.
This granularity strikes a crucial balance: unlike releases, it retains the fine-grained development dependencies and structural evolution of the codebase; unlike commits, it encapsulates realistic and coherent functional goals.
Functional dependencies among milestones naturally form a Directed Acyclic Graph (DAG), which captures genuine prerequisite constraints while allowing independent features to proceed in parallel.
However, constructing milestone DAGs requires reordering and grouping commits, which disrupts the native git history.
This poses a severe challenge to correctness: applying reordered patches often breaks compilation and test collection, jeopardizing the benchmark’s executability and realism.

To resolve this, we introduce DeepCommit, an automated agentic pipeline that reconstructs verifiable software evolution itineraries in the form of Milestone DAGs.
By synergizing static analysis, LLM-agent-driven milestone construction, and runtime validation, DeepCommit ensures the synthesized milestones are executable and testable.
Powered by Claude Opus 4.5, it achieves a high average test collection success rate of $>$85%, ensuring comprehensive verification coverage.
Designed as a scalable agentic framework, DeepCommit is poised to leverage future LLM advancements to harvest increasingly accurate and extensive evolution itineraries from the vast open-source ecosystem.

Building on this foundation, we present EvoClaw, a benchmark for evaluating LLM agents under continuous software evolution.
EvoClaw comprises 98 human-verified milestones across 7
evolution itineraries (milestone DAGs), each from a release range of a unique high-impact open-source Repository, and spanning five programming languages.
Rather than solving independent tasks, agents in EvoClaw are tasked with evolving a codebase through streams of these dependency-constrained milestones, closely mirroring real-world development scenarios.
A single full evaluation costs approximately $500 with frontier models such as Claude Opus 4.5.
To achieve a high score in this setting, an agent must maintain long-term context, manage architectural consistency, and prevent error accumulation across extended development horizons.

Using EvoClaw, we conduct a comprehensive evaluation of 4 frontier agent frameworks and 10 state-of-the-art LLMs. We assess performance using a unified Score (Section 5.1), which balances Recall (completeness of new feature implementation) and Precision (robustness against regressions), along with a strict Resolve Rate for fully completed milestones. Our evaluation reveals the following key findings regarding agent capabilities in continuous software evolution:

A fundamental performance gap: Continuous vs. Independent. (Section 5.2) Frontier models exhibit a substantial degradation from independent to continuous task evaluation.
Scores drop from over $\sim$80% on isolated tasks to at most 38.03% (Claude Opus 4.6) in continuous environments, with a mere 13.37% Resolve Rate (Gemini 3 Pro).

Recall grows linearly but Precision saturates. We identify a fundamental asymmetry in continuous software evolution (Section 5.4): while frontier agents retain the capability to implement new features (linear Recall growth), they fail to prevent regressions as the system evolves (saturated Precision). This indicates that agents struggle primarily with system-level maintenance rather than local implementation.

Accumulated errors stall downstream progress. Unresolved regressions trigger a “snowball effect” where errors accumulate faster than agents can fix them (Section 5.5). Early bugs propagate through dependency chains to contaminate downstream tasks, eventually stalling development entirely.

Proactive exploration and verification mitigate technical debt. Behavioral analysis shows that successful sustained evolution relies on proactive codebase exploration and disciplined test verification, whereas both blind trial-and-error and the absence of verification accelerate failure (Section 5.6).

### Related Work

LLM-Driven Coding Agents.
While basic Bash tools provide a foundation for interacting with the environment, equipping LLMs with specialized scaffolding significantly enhances efficiency, reliability, and user-friendliness.
SWE-agent (Yang et al., 2024) introduced the Agent-Computer Interface (ACI), mini-SWE-agent (Lieret et al., 2025) demonstrated that a minimal 100-line agent can remain competitive, and OpenHands (Wang et al., 2024) targets end-to-end autonomous issue resolution.
Commercial tools span diverse integration paradigms: Devin (Labs, 2024) pioneered fully autonomous software engineering, GitHub Copilot (GitHub, 2025), Cursor (Cursor, 2024), Trae (ByteDance, 2025), and Antigravity (Google, 2025a) embed agents within IDE or cloud workflows, while Claude Code (Anthropic, 2025), Codex (OpenAI, 2025), and Gemini CLI (Google, 2025b) provide terminal-based execution.
Despite these distinct paradigms, all major platforms have converged on providing terminal-based agentic interfaces, which is the modality we adopt for evaluation in this work.
As LLMs grow more capable, agent scaffolds evolve to grant greater autonomy, supporting long-horizon tasks with complex dependencies.

Software Engineering Benchmarks for LLMs.

Recent benchmarks have progressed from isolated function completion to realistic codebase generation evaluations.
SWE-bench (Jimenez et al., 2024) introduced issue resolution in real-world codebases, followed by quality-controlled variants such as SWE-bench Verified (Chowdhury et al., 2024), SWE-bench Pro (Deng et al., 2025), and multilingual extensions in Multi-SWE-bench (Zan et al., 2025).
Beyond issue fixing, SWE-Evo (Thai et al., 2025) and Commit-0 (Zhao et al., 2025) explore longer-horizon development workflows, NL2Repo (Ding et al., 2026) evaluates full repository generation from natural-language specifications, and automated pipelines such as SWE-rebench (Badertdinov et al., 2025) and SWE-bench Live (Zhang et al., 2025) improve realism and data hygiene.
Despite these advances, most benchmarks model software engineering as static, independent tasks.
This overlooks the continuous, dependency-driven nature of real-world software evolution (Yao, 2025) and underutilizes the rich developmental structure encoded in version histories.
Consequently, current evaluations primarily measure short-horizon task completion rather than sustained codebase evolution.

### DeepCommit: An Automated Pipeline for Reconstructing Software Evolution

#### From Raw Commits to Milestone DAGs

Software repositories encode rich evolutionary trajectories, yet raw commit histories remain noisy, fragmented, and inadequate as executable development sequences.
Commits vary widely in granularity, semantic clarity, and dependency structure, while parallel branches, squash merges, and non-functional changes obscure true developmental relationships.
Relying on documentation or release notes alone lacks sufficient resolution to reconstruct precise code evolution.
DeepCommit addresses this challenge by transforming linear git histories into structured, verifiable Milestone DAGs, where each node represents a coherent, testable unit of development and edges encode dependency constraints across evolution phases.

#### Overall Agent-Driven Pipeline

As illustrated in Figure˜2, DeepCommit reconstructs software evolution itineraries through an end-to-end pipeline that sequentially integrates: (1) commit history preprocessing, (2) milestone DAG construction, and (3) executable environment resolution.

###### Commit History Preprocessing

Given a development window defined by version tags, we collect all main-branch commits together with associated Pull Requests (PRs), Issues, Releases, and discussion metadata, providing both structural and semantic context for downstream reconstruction (details in Appendix A).
We filter out commits that only touch non-source files (e.g., docs, CI configs) using a per-repo source-directory whitelist.

To facilitate milestone discovery and dependency inference, we extract multi-dimensional structural signals through static analysis.
Specifically, we construct: (1) a commit-level DAG using git blame to trace line-level textual dependencies; (2) symbol-level modifications identifying key changes in classes and functions; and (3) file-level co-change statistics to reflect evolutionary coupling.

###### Milestone DAG Construction

Organizing hundreds of discrete commits into semantically coherent milestones requires integrating structural dependencies with code-level reasoning. We employ a four-stage LLM-agent-driven process to progressively construct the Milestone DAG, where each stage is orchestrated with automated data preparation, agent-accessible validation tools for self-checking, and post-process quality gates that trigger re-execution upon failure.

Seed Discovery.
An LLM agent identifies foundational milestone anchors by jointly evaluating DAG topology (e.g., high out-degree and descendant count), commit semantics, and evolutionary patterns. Commits that initiate distinct development themes, rather than mere incremental follow-ups, are selected as seeds for subsequent milestone construction.

Milestone Consolidation.
For each seed, parallel sub-agents aggregate semantically and structurally related commits.
A coordinating agent then resolves overlaps, enforces complete coverage, and guarantees an acyclic partition in which each commit belongs to exactly one milestone.

Dependency Inference.
Candidate inter-milestone edges are proposed based on commit-level dependencies, file co-change patterns, and symbol-level dependencies, and subsequently validated through agent-based semantic reasoning.

Granularity Refinement.
Oversized milestones are decomposed into semantically independent sub-milestones, while underspecified ones are merged into adjacent milestones.
Dependencies are synchronously updated to preserve a valid DAG structure (details in Appendix B).

###### Runtime Environment Resolution

To transform the Milestone DAG into an executable evaluation environment, we use a multi-agent workflow
that generates reproducible Docker images and stable test behaviors for each milestone by automatically resolving runtime dependencies and test framework configurations.

Milestone Optimization and Testbed Preparation.
A MilestoneAgent reconstructs repository states by sequentially cherry-picking milestone commits in topological order.
When build failures arise from misattributed commits or missing dependencies, the Main Agent triggers iterative DAG refinement and testbed regeneration.

Environment Configuration.
An EnvAgent configures runtime environments by leveraging repository CI/CD workflows and automatically generating Dockerfiles for each milestone.
Build issues at this stage are resolved by adjusting the Dockerfile (e.g., installing missing dependencies, pinning compatible versions); persistent errors signal upstream DAG inconsistencies requiring further refinement.

Test Collection.
For each milestone, we define a START state (post-prerequisite completion) and an END state (post-implementation).
Tests are executed before and after applying gold patches, repeatedly filtering flaky behaviors.
Stable transitions are categorized as Fail-to-Pass (F2P) to validate newly introduced functionality and Pass-to-Pass (P2P) to enforce regression preservation (Appendix C).

#### Automated Quality Assurance

To ensure the reliability and reproducibility of our evaluation, we rigorously validate each milestone testbed across three core dimensions:

Milestone Graph Validity. We verify the structural integrity of the reconstructed history. This includes confirming commit completeness (100% coverage of the target range), dependency consistency (ensuring milestone dependencies respect underlying commit dependencies), and DAG correctness (validating acyclicity).

Runtime Executability. We ensure that errors stem from agent code, not infrastructure. We verify testbed compilability by ensuring successful build and test collection in both states. We also strictly monitor execution logs to ensure environment-induced errors remain negligible.

Evaluation Reliability. We assess the stability of the test suites. We achieve a high test collection rate (87.1%). We ensure test consistency by validating a negligible Pass-to-Fail rate ($\leq$0.026%) and filtering flaky tests through multiple runs. Finally, we enforce retained milestone to have at least one F2P or N2P test signal (details in Appendix D).

##### Commit History Preprocessing

Given a development window defined by version tags, we collect all main-branch commits together with associated Pull Requests (PRs), Issues, Releases, and discussion metadata, providing both structural and semantic context for downstream reconstruction (details in Appendix A).
We filter out commits that only touch non-source files (e.g., docs, CI configs) using a per-repo source-directory whitelist.

To facilitate milestone discovery and dependency inference, we extract multi-dimensional structural signals through static analysis.
Specifically, we construct: (1) a commit-level DAG using git blame to trace line-level textual dependencies; (2) symbol-level modifications identifying key changes in classes and functions; and (3) file-level co-change statistics to reflect evolutionary coupling.

##### Milestone DAG Construction

Organizing hundreds of discrete commits into semantically coherent milestones requires integrating structural dependencies with code-level reasoning. We employ a four-stage LLM-agent-driven process to progressively construct the Milestone DAG, where each stage is orchestrated with automated data preparation, agent-accessible validation tools for self-checking, and post-process quality gates that trigger re-execution upon failure.

Seed Discovery.
An LLM agent identifies foundational milestone anchors by jointly evaluating DAG topology (e.g., high out-degree and descendant count), commit semantics, and evolutionary patterns. Commits that initiate distinct development themes, rather than mere incremental follow-ups, are selected as seeds for subsequent milestone construction.

Milestone Consolidation.
For each seed, parallel sub-agents aggregate semantically and structurally related commits.
A coordinating agent then resolves overlaps, enforces complete coverage, and guarantees an acyclic partition in which each commit belongs to exactly one milestone.

Dependency Inference.
Candidate inter-milestone edges are proposed based on commit-level dependencies, file co-change patterns, and symbol-level dependencies, and subsequently validated through agent-based semantic reasoning.

Granularity Refinement.
Oversized milestones are decomposed into semantically independent sub-milestones, while underspecified ones are merged into adjacent milestones.
Dependencies are synchronously updated to preserve a valid DAG structure (details in Appendix B).

##### Runtime Environment Resolution

To transform the Milestone DAG into an executable evaluation environment, we use a multi-agent workflow
that generates reproducible Docker images and stable test behaviors for each milestone by automatically resolving runtime dependencies and test framework configurations.

Milestone Optimization and Testbed Preparation.
A MilestoneAgent reconstructs repository states by sequentially cherry-picking milestone commits in topological order.
When build failures arise from misattributed commits or missing dependencies, the Main Agent triggers iterative DAG refinement and testbed regeneration.

Environment Configuration.
An EnvAgent configures runtime environments by leveraging repository CI/CD workflows and automatically generating Dockerfiles for each milestone.
Build issues at this stage are resolved by adjusting the Dockerfile (e.g., installing missing dependencies, pinning compatible versions); persistent errors signal upstream DAG inconsistencies requiring further refinement.

Test Collection.
For each milestone, we define a START state (post-prerequisite completion) and an END state (post-implementation).
Tests are executed before and after applying gold patches, repeatedly filtering flaky behaviors.
Stable transitions are categorized as Fail-to-Pass (F2P) to validate newly introduced functionality and Pass-to-Pass (P2P) to enforce regression preservation (Appendix C).

### EvoClaw: Benchmarking Continuous Software Evolution

EvoClaw introduces a novel evaluation paradigm designed to assess an agent’s ability to evolve and maintain a software codebase over an extended lifecycle.
As shown in Figure˜3, unlike traditional benchmarks that focus on resolving independent issues,
EvoClaw simulates a realistic, continuous development process where requirements arrive as a stream, and tasks have strict sequential dependencies.

#### The Continuous Task Evaluation Framework

The framework orchestrates a continuous development pipeline: an external planner dynamically unlocks tasks based on a dependency graph, the agent implements them in a persistent codebase, and the framework asynchronously evaluates snapshots upon submission. This design explicitly decouples roadmap planning from implementation, allowing us to assess the agent’s ability to maintain and evolve software within a structured workflow.
The framework comprises three core components:

Dependency-Driven Task Stream. Requirements are not presented in a static batch but are unlocked dynamically. The system maintains a DAG-based task scheduler where a new milestone $M_{i}$ becomes available to the agent if and only if all its prerequisite milestones $\{M_{j}\mid M_{i}\mathrel{depends}\,\mathrel{on}M_{j}\}$ have been completed. This simulates real-world constraints in which foundational features must be established before dependent features are implemented.

Continuous Evolution Environment. The agent operates within a persistent, stateful environment where modifications from each task persist into the next. This compels the agent to maintain the long-term health of the codebase, as early technical debt or latent bugs can accumulate and impede future progress.

Snapshot-Based Isolated Evaluation. To reconcile the need for a continuous development flow with rigorous verification, we employ a “develop-in-place, evaluate-in-isolation” strategy. Upon task completion, the agent’s implementation state is snapshotted and transferred to an isolated evaluation container to run the test suite. This ensures that the scoring process is reproducible and unaffected by the agent’s ongoing development, while the agent’s working environment remains uninterrupted.

#### Benchmark Construction

We construct a high-quality dataset through a rigorous pipeline that transforms open-source repositories into verified evolutionary suites.

Repository and Range Selection. We identify projects with high community impact and diverse programming languages. We specifically select release ranges that exhibit rich dependency structures, ensuring the benchmark captures complex, non-linear development scenarios rather than trivial sequences.

Itinerary Extraction via DeepCommit.
Leveraging the DeepCommit pipeline (Section 3), we mine the evolutionary history of selected projects.
To guarantee the benchmark’s quality and evaluation efficiency, we apply strict post-processing filters to the generated milestones.
We retain only milestones that: (1) represent core functional changes (filtering out pure documentation updates); (2) possess executable F2P tests to serve as definitive success criteria; and (3) fall within a manageable context window to maintain task solvability.
This step ensures that every task in the benchmark is grounded in a verified, executable state transition.

Reverse-Engineering Software Requirement Specifications (SRS).
Relying solely on original GitHub issues or PR descriptions is often insufficient, as they can be underspecified, outdated, or disconnected from the final code implementation.
To bridge this gap, we employ an agent-driven reverse-engineering approach to synthesize high-fidelity Software Requirement Specifications (SRS).
We first dispatch an LLM agent to analyze the ground-truth patches to draft precise functional requirements.
This draft then undergoes a refinement phase to align acceptance criteria strictly with the verified Fail-to-Pass tests.
Finally, environment-specific instructions (e.g., dependency updates) are appended by analyzing build configuration changes, ensuring a complete execution context.

Human-in-the-Loop Verification.
Automated generation can yield logical inconsistencies and misalignment with edge cases. To mitigate this, expert annotators conduct a final review focused on task solvability.
Annotators verify that the SRS provides all necessary information to solve the problem without leaking implementation details and that the acceptance criteria are unambiguous.
Simultaneously, we validate the stability of the test suites to rule out flaky tests.
This hybrid verification ensures that EvoClaw provides a fair assessment, distinguishing genuine agent errors from artifacts of ambiguous specifications.

#### Benchmark Statistics

EvoClaw comprises 98 verified milestones across 7 diverse open-source repositories, spanning five programming languages (Go, Rust, Java, TypeScript, Python) with a total of 124 inter-milestone dependencies. As shown in Figure˜4(a), the milestones are distributed across repositories with varying complexity, ranging from 9 to 23 milestones per repository.
The dataset captures diverse real-world development patterns, including major architectural changes (e.g., multi-library support), feature-rich iterations (e.g., cloud-native enhancements), stability-focused releases (e.g., compatibility fixes), and large-scale refactoring (e.g., type system overhauls). This ensures EvoClaw evaluates agents across the full spectrum of software engineering tasks.

Figure˜4(b) illustrates the distribution of task complexity. The dataset exhibits substantial diversity in both specification length (SRS mean: 1,348 words) and implementation scope (gold patch LOC ranging from $<100$ to $>1,500$). On average, each milestone modifies 27.4 files and involves 17.1 Fail-to-Pass tests for verification alongside 6,218 Pass-to-Pass tests for regression prevention. Detailed per-repository statistics are provided in Appendix F, and the full Milestone DAG visualizations for all repositories are shown in Appendix G.

### Results and Analysis

#### Experimental Setup

#### Overall Performance

Table 2 presents results across 15 agent-model configurations.
Claude Opus 4.6 achieves the highest Score (38.03% in Openhands and 36.29% in Claude Code), followed by Claude Sonnet 4.6 (29.58%) and GPT 5.3-Codex (28.88%).
Across all models, the gap between Score ($\sim$38% at best) and Resolve Rate ($\sim$13%) is substantial: agents achieve partial progress on most milestones but rarely complete them fully.
Moreover, the resolved milestones are predominantly early ones with few upstream dependencies, confirming that accumulated upstream errors increasingly hinder downstream task completion.
Unless otherwise noted, subsequent analyses focus on configurations where each model is paired with its vendor-provided agent framework.

Comparing across model families, clear generational improvements emerge: Claude 4.6 models significantly outperform their 4.5 predecessors, and GPT 5.3-Codex substantially improves over both GPT 5.2-Codex and GPT 5.2. However, comparing GPT 5.2 and GPT 5.2-Codex reveals that Codex-specific optimization may be counterproductive for long-horizon development, where sustained codebase maintenance demands broader analytical capabilities beyond isolated task solving.
The three Gemini models achieve comparable scores, with Gemini 3 Flash matching Gemini 3 Pro at one-ninth the cost. Gemini 3 Pro uses the fewest turns, possibly indicating insufficient exploration.
Figure 6 visualizes the cost-score trade-off. Higher cost does not uniformly translate into higher performance: Gemini 3 Pro and Sonnet 4.6 both exceed $100 per evolution range yet score below Opus 4.6 ($88). On the Pareto frontier, Gemini 3 Flash ($12, 24.2%) and GPT 5.3-Codex ($25, 28.9%) offer the best cost-effectiveness, achieving competitive scores at a fraction of the cost of top-performing models.
OpenHands trials exhibit notably longer execution times (e.g., 18.49 h for GPT 5.3-Codex) because its runner permits up to 3,000 iterations per milestone with automatic session resumption, allowing the agent to retry extensively when stuck. This additional compute does not consistently improve scores: Claude Code with Opus 4.6 achieves a comparable score in under 4 hours.

Additionally, Figure 5 compares per-repository performance under both evaluation modes. High independent-task performance across all repositories confirms that milestones are individually solvable, indicating that the difficulty stems from long-horizon error accumulation rather than inherent task complexity.
This effect varies significantly by repository. scikit-learn exhibits the largest degradation: Claude Sonnet 4.6 achieves 93.2% independently but only 21.1% under continuous evaluation.

Overall, these results highlight that EvoClaw poses a significant challenge to current frontier models, and reliable long-horizon continuous development remains an open problem.

#### Task Complexity and Topological Effects

Figure 7 examines how milestone characteristics correlate with agent performance.
Gold patch LOC, a traditional measure of task complexity, shows a clear monotonic relationship. Larger patches require more code changes and yield lower scores across all models.
SRS (Software Requirements Specification) word count, however, exhibits a non-monotonic pattern, with a clear sweet spot for specifications of moderate length (around 500 to 1500 words). When specifications are concise, agents must autonomously locate relevant context from the repository, increasing exploration burden. When specifications are verbose, the sheer volume of requirements increases implementation workload. Milestones with moderate-length SRSs achieve the highest accuracy, suggesting that task difficulty depends not only on implementation effort but also on the cost of information acquisition.

Beyond these static factors, the continuous evaluation setting introduces structural complexity unique to EvoClaw. Both the milestone execution order and the DAG topological layer show statistically significant negative correlations with the score. Later milestones and deeper topological layers consistently yield lower performance. This reflects the compounding effect of upstream errors, as agents must build upon their own (potentially flawed) prior work. These topological factors are absent in independent evaluation and represent the distinctive challenge of long-horizon software evolution.
The Resolve Rate (bottom row of Figure 7) makes this effect even starker: it drops drastically beyond the earliest milestones and the shallowest DAG layers, indicating that current agents can only fully resolve milestones that appear early in the sequence or have no upstream dependencies. Once prior errors accumulate, agents may still achieve partial progress (reflected in Score) but rarely produce a completely correct solution.

#### Evolution Dynamics: Recall Scales while Precision Saturates

The declining performance at later milestones raises a natural question: does agent capability degrade over time, or does accumulated technical debt overwhelm otherwise competent agents?

To answer this, we model cumulative score trajectories using a saturation function $y=a(1-e^{-bx})$, where a small $b$ yields near-linear growth while a large $b$ produces rapid saturation toward the ceiling $a$. As shown in Figure 8 (left), all models under continuous evaluation exhibit clear performance ceilings, and multi-window extrapolation (fitting the saturation model to progressively larger subsets of milestones and projecting forward) confirms that these ceilings persist beyond the observed window. Comparing continuous and independent evaluation (center, right), independent scores grow near-linearly while continuous scores saturate, with the gap widening monotonically as evolution progresses.

We decompose the cumulative score into Recall (successful feature implementation) and Precision (preservation of existing functionality) to isolate the underlying mechanism. Figure 9 reveals a fundamental asymmetry: Recall continues to grow near-linearly across all models (especially frontier models), indicating that agents retain the ability to solve newly assigned tasks. Precision, however, saturates rapidly across all evaluated configurations. This means the performance ceiling is not caused by agents forgetting how to code, but by their inability to prevent regressions from accumulating. Stronger models achieve higher Precision plateaus, yet none avoid saturation entirely. This Recall-Precision divergence provides a mechanistic explanation for the snowball effect: as unresolved regressions compound, each new milestone operates on an increasingly degraded codebase, eventually overwhelming the agent’s capacity for productive development.

#### Failure Analysis: Error Generation and Propagation

Understanding why agents fail in continuous evaluation is inherently difficult. A single early mistake can trigger cascading test failures across dozens of downstream milestones, making it challenging to disentangle root causes from their propagated consequences.
To enable systematic analysis, we introduce the concept of error chains: for each test that transitions from passing to failing during the evolution, we trace its status across all subsequent milestones until it is either healed or the trial ends. This yields a per-test timeline that captures the full lifecycle of an error.
We focus this analysis on the strongest configuration, Claude Opus 4.6, to characterize failure mechanisms at the frontier of current agent capabilities.

We decompose error chains along two orthogonal dimensions. The first, Propagation Type, captures how a fault affects downstream milestones. This is determined statistically from evaluation results: we track each test’s status across the milestone timeline and classify events as P0 Root Cause (the originating failure), P0 Induced (cross-chain contamination from unrelated changes), P1 Inherited (propagated through dependency), PX Missing (skipped execution), or PH Healed (successfully recovered).
Figure 10 (right) shows that propagation events (P1, PX) increasingly dominate in later stages, confirming the compounding degradation observed in Section 5.3. The left panel visualizes representative error chain patterns across repositories, illustrating how a single root cause event can cascade through the entire remaining evolution.

The second dimension, Root Cause Type, captures why the initial fault originates. Since root cause attribution requires understanding the agent’s intent, we employ Claude Sonnet 4.6 as a reviewer agent that compares the task agent’s code changes against the ground-truth patch, the SRS specification, and evaluation artifacts. The reviewer classifies each error chain’s root cause into three categories: Logic Error (correct target, buggy implementation), Omission (missing a required component), or Extraneous (unnecessary modifications that break existing functionality).
Figure 11 presents the joint distribution of Root Cause Type $\times$ Propagation Type. Logic Error is the dominant root cause ($\sim$57% of all error chain events), with its chains exhibiting both the highest inherited propagation (P1, 12%) and the highest proportion of missing test execution (PX Missing, 17%), indicating that buggy implementations frequently prevent downstream tests from running at all.

#### Agent Behavior: The Struggle Against Accumulating Complexity

Beyond aggregate scores, we examine how agents allocate effort and manage state when facing accumulating technical debt during long-horizon iterations. By instrumenting tool calls, context usage, and interaction turns, we reveal distinct behavioral patterns.

Effort Fluctuation and Extremes. As shown in Figure 12, all evaluated agents exhibit a shared trend in their effort allocation (measured by the continuous-to-independent turns ratio). In the initial phase (progress $\sim$0.1), continuous effort is slightly higher than independent effort, as agents must conduct large-scale exploration to build a mental model of the unfamiliar repository. During the middle phase (progress 0.1–0.5), the ratio drops below $1\times$ (with the median falling to $\sim$0.83$\times$): agents successfully reuse their established context, bypassing the redundant exploration required in independent evaluation. However, in the late stage (progress 0.6–0.9), effort rises significantly as accumulating errors demand extensive debugging. Finally, near completion (progress $\sim$1.0), agent behavior diverges sharply. Some agents resort to frantic thrashing, while others prematurely give up. Notably, GPT 5.3-Codex demonstrates the most stable effort profile, maintaining consistent variance throughout the project lifecycle.

Context Stability and Exploration Patterns. To sustain this fluctuating effort, agents must effectively manage their context. Figure 13 illustrates this using Claude Code with Opus 4.6 as a representative example. The context window shows stable, controllable wave patterns, demonstrating that modern agent frameworks paired with frontier models can effectively support long-horizon programming without catastrophic context overflow. The framework employs two compression strategies: partial compression (evicting specific tool results) and heavy compaction (summarizing extensive histories). Crucially, agent exploration behavior (reading and searching) tightly couples with this state management. Exploration surges at the beginning of each new milestone and immediately following major context compaction events, as the agent works to rebuild its mental model.

The Impact of Exploration. This exploration behavior directly dictates downstream success. Figure 14 demonstrates that within their respective agent frameworks, models from the same family exhibit a consistent pattern: higher exploration counts correlate with better performance. For instance, Claude Opus 4.6 and Claude Sonnet 4.6 hold a distinct advantage because they aggressively dispatch subagents to analyze the codebase, executing over 7,000 exploration commands. Conversely, models like Gemini 3 Pro allocate too little effort to reading, indicating that many current models still lack proactive exploration for long-horizon tasks.

Verification vs. Blind Thrashing. Alongside exploration, we analyze verification behavior (test execution). Figure 15 shows that average verification effort generally follows an inverted-U shape, increasing as the codebase grows more complex before declining near the end. However, this masks two problematic extremes: Gemini 3.1 Pro verifies excessively, while GPT 5.2-Codex rarely verifies at all, and both achieve lower scores. Figure 16 further isolates this dynamic by mapping the score landscape against edit thrashing and verification frequency. A clear sweet spot emerges for moderate, disciplined verification. In contrast, the worst outcomes concentrate in the high-thrash and low-verify quadrant—a blind thrashing trap where agents repeatedly modify the same files without executing tests to guide them, effectively accelerating the snowball effect.

#### DeepCommit vs Human-Annotated Milestone DAG

We conducted a case study (Appendix J) that compares the human-annotated and DeepCommit milestone DAGs for the scikit-learn v1.5.2–v1.6.0 release interval. The Human DAG organizes milestones by semantic release intent, whereas DeepCommit derives groups from dependency topology in the commit graph. As a result, DeepCommit covers a smaller but tightly connected subset of commits, recovers human-like boundaries when technical structure is clear (e.g., documentation), but tends to fragment cross-module, intent-defined milestones into topological phases. Overall, this case study shows that the Human DAG captures semantically coherent and process-aware milestone structure, whereas DeepCommit more strongly reflects dependency topology and phase-wise code organization.

### Conclusion

We introduced DeepCommit, a pipeline that distills verifiable software evolution into coherent Milestone DAGs from noisy, fine-grained git histories, and EvoClaw, a benchmark for evaluating LLM agents under continuous, dependency-driven development. Our results reveal a fundamental gap between independent task-solving and continuous evolution: frontier models achieve over 80% on isolated milestones but drop below 38% in continuous settings. This degradation stems from a critical inability to maintain code integrity: while agents can implement new features, they fail to prevent regressions, causing a snowball effect of accumulating technical debt. Even the strongest agents resolve only $\sim$13% of milestones in full evolutionary sequences, establishing sustained, maintainable repository evolution as a central open challenge for autonomous software agents.

### Impact Statement

This paper presents a benchmark for evaluating LLM agents in continuous software evolution, a prerequisite for deploying autonomous agents in real-world production environments. Beyond code generation, we emphasize the ability to sustainably evolve systems over time, which is essential for long-running agent runtimes to iteratively customize software for diverse user needs. This capability unlocks a new productivity paradigm: agents serving as adaptive interfaces that bridge human intent and complex digital systems. Although highly capable coding agents may impact the software development workforce, we expect them to lower the barrier to entry for software creation, empowering a broader range of users to leverage the power of code for problem-solving
