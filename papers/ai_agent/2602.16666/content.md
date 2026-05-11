# Towards a Science of AI Agent Reliability

**Authors:** Stephan Rabanser Sayash Kapoor Peter Kirgis Kangheng Liu Saiteja Utpala Arvind Narayanan Princeton University

## Abstract

AI agents are increasingly deployed to execute important tasks. While rising accuracy scores on standard benchmarks suggest rapid progress, many agents still continue to fail in practice. This discrepancy highlights a major limitation of current evaluations: focusing on a single metric is not enough to understand agent behavior. Notably, it ignores whether agents behave consistently across runs, withstand perturbations, fail predictably, or have bounded error severity. Grounded in safety-critical engineering, we provide a holistic performance profile consisting of twelve metrics that decompose agent reliability along four key dimensions: consistency, robustness, predictability, and safety. Evaluating 14 models across two complementary benchmarks, we find that recent capability gains have only yielded small improvements in reliability. By exposing these persistent limitations, our metrics complement traditional evaluations while offering tools for reasoning about how agents perform, degrade, and fail.

### 1 Introduction

AI agents are rapidly transitioning from research prototypes to deployed systems that perform increasingly consequential tasks autonomously: modifying code [69], managing databases [62], browsing the web [11], and orchestrating complex multi-step workflows [70].
The promise of such agents is substantial and widely recognized. If they performed reliably, they could automate significant fractions of routine work and augment human capability across domains.
Yet the same autonomy that makes these agents useful also makes their failures costly. While many standard evaluations suggest these systems are ready for such responsibilities, recent high-profile incidents have exposed a troubling gap between benchmark performance and real-world outcomes [48].

In July 2025, Replit’s AI coding assistant deleted an entire production database despite explicit instructions forbidding such changes [8, 58]. Months earlier, Washington Post columnist Geoffrey Fowler asked OpenAI’s Operator to find “cheap eggs” for delivery, only to find that the agent made an unauthorized $31.43 purchase from Instacart, violating the company’s user confirmation safeguard before purchases [20, 46]. In 2024, the New York City government launched a chatbot for business assistance which consistently provided illegal advice and gave different (incorrect) answers to ten journalists asking the same question [34]. In each case, agents were judged to be reasonably capable by internal assessments, but displayed unreliable performance in real-world deployment, leading to costly failures.
This raises a fundamental question:

How should we define and evaluate agent reliability?

The dominant paradigm for agent evaluation offers little help in answering this question.
Despite recent efforts of providing a more holistic evaluation of agents [31] and the language models that drive them [37], standard evaluation practice centers on reporting mean task success rates [76, 27, 40, 42]: the percentage of benchmark tasks an agent completes correctly.
This approach has clear advantages: it is simple to compute, easy to compare across systems, and provides a clean optimization target. But it obscures the behavioral properties that matter most for deployment. Accuracy cannot distinguish an agent that fails on a fixed, identifiable subset of tasks from one that fails unpredictably with the same rate. Yet the former permits a partitioning of tasks between humans and agents, while the latter does not.
Accuracy also cannot distinguish benign failures (incomplete outputs, formatting errors) from catastrophic ones (deleted files, unauthorized actions), even though no practitioner would view them as interchangeable.
Standard benchmarks do not report sensitivity to input perturbations, nor do they assess whether agents can recognize when they are likely to fail and abstain from returning bad predictions.

This evaluation gap stands in stark contrast to safety-critical engineering.
In aviation [54, 50], nuclear power [25], automotive [26], and railway systems [14], reliability has long been understood as a critical, multi-dimensional property [24, 4, 33], and recent work has argued for applying these system safety principles to AI [12, 51].
Certification requires not only that systems perform correctly on average, but that they behave consistently across executions, bound the severity of failures, and degrade predictably under stress.
These domains assess failure probability and failure consequence separately: a component that fails rarely but catastrophically when it does may be less acceptable than one that fails more often but always benignly.
They quantify tail risks explicitly, asking not just “what is the average outcome?” but “how bad can the worst outcomes be, and how often do they occur?”.
Finally, they test systems under structured perturbations, such as varying inputs, environmental conditions, and component behaviors, to characterize how performance degrades outside nominal operating conditions.

We adapt the safety-critical perspective to agent evaluations, decomposing reliability into four dimensions (see Table 1): consistency (repeatable behavior across runs), robustness (stability under input and environmental perturbations), predictability (calibrated confidence and discrimination of correct/incorrect predictions), and safety (bounded severity when failures occur).
Each dimension captures a property that matters for deployment but cannot be measured by accuracy alone.
Across these dimensions, we propose a total of twelve concrete metrics that are independent of raw accuracy (see Section 3), enabling comparison of reliability across agents with different capability levels.

Applying these metrics to 14 models across two benchmarks, we find that reliability gains lag noticeably behind capability progress (see Figure 1): despite steady accuracy improvements over 18 months of model releases, reliability only shows modest overall improvement. To analyze this widening gap, our paper provides two key contributions:

A formal taxonomy and suite of metrics: We translate qualitative safety-critical principles into computable metrics, enabling evaluation of agent reliability independently of task success.

A comprehensive reliability profile of modern agents: A detailed mapping of where state-of-the-art models succeed and fail, isolating consistency and predictability as the dimensions requiring immediate research focus.

### 2 A Cross-Domain Perspective of Reliability

Before defining reliability metrics for AI agents, we take a step back to ask the foundational question: what is reliability, and how have engineering disciplines with long traditions of building dependable systems approached it?
This section synthesizes decades of practice from safety-critical engineering into a unified decomposition, connecting each dimension to existing work in machine learning.

To that end, we survey reliability practices across safety-critical industries—aviation, nuclear power, automotive systems, and industrial process control—to identify recurring evaluation dimensions (see Appendix B.2 for details). Despite substantial differences in technology, regulation, and risk tolerance, four dimensions emerge, summarized in Table 1. This convergence across independent fields suggests these dimensions capture fundamental aspects of reliability rather than domain-specific concerns.

Across safety-critical domains, variance itself is treated as a liability: flight-critical software must behave deterministically, reactor protection systems must respond identically each time conditions warrant shutdown, and process control systems flag unexpected variance before it cascades into larger problems. The principle is that even acceptable average performance becomes problematic when high variance makes outcomes unpredictable.
While ML research has documented numerous instances of this problem—including prompt sensitivity [52], floating-point non-determinism [22], and a growing disconnect between capability and consistency [64]— these are typically treated as isolated phenomena rather than symptoms of a unified reliability deficit. Recent efforts have begun to formalize these individual concerns; for instance, evaluating consistency by prioritizing pass$\wedge k$ [71] over traditional pass$@k$. 11pass$@k$ measures best-case capability by requiring at least one success in $k$ attempts, whereas pass$\wedge k$ measures strict consistency by demanding success across all $k$ attempts. However, a comprehensive framework connecting these ad-hoc observations to safety-critical engineering practice remains largely absent.

Real-world systems rarely operate under ideal conditions. Automotive safety testing evaluates responses to sensor failures and adverse weather; aviation qualification tests hardware against temperature extremes, vibration, and electromagnetic interference; chemical plants analyze how process deviations propagate through interconnected systems. The common thread is that robust systems degrade gracefully rather than failing abruptly.
While ML research has identified various specific failure modes, such as sensitivity to input variations [65, 6] and susceptibility to prompt injection [44], these are often treated as disparate phenomena instead of components of a broader, unified account of robustness.

A system that fails in known, expected ways is often preferable to one that fails rarely but unpredictably. Nuclear risk assessment explicitly models failure modes and quantifies their probabilities; aviation certification categorizes failures by severity and assigns probability targets; many safety systems employ “safe modes” with reduced functionality but guaranteed safety when uncertainty exceeds thresholds. The key insight: systems should know what they do not know.
ML research on calibration [21, 39, 36] and selective prediction [13, 29, 3, 49] addresses related concerns, though often without connecting to the broader notion of predictable failure behavior that safety-critical domains emphasize.

Every safety-critical field ties reliability to consequence-aware risk assessment. Nuclear safety computes not just failure frequencies but expected consequences: health effects, economic impacts, environmental damage. Process industry standards tie development rigor to the failure severity. Aviation targets catastrophic failure probabilities below one in a billion per flight hour. The unifying principle is that not all failures are equal. ML evaluation of safety has largely focused on compliance with harmful requests [2] or specific harmful behaviors like sycophancy [47]. These are important concerns for model deployment and governance, but distinct from consequence-aware assessment of how agents fail at legitimate tasks.

### 3 Operationalizing Reliability for AI Agents

Building on the reliability dimensions identified across disciplines from Section 2, we now operationalize these concepts for AI agents. Table 2 provides formal definitions of our full metric suite. Here, we offer intuition for why each dimension and its constituent metrics matter for agent deployments.

#### Consistency (RCon\mathcal{R}_{\text{Con}})

A reliable agent should produce similar results when faced with identical conditions. Unlike traditional software, where deterministic execution is the norm, language model-based agents exhibit inherent stochasticity. This variability becomes problematic when users cannot predict whether re-running a task will yield the same outcome, follow the same solution approach, or incur similar costs at deployment time.

We decompose consistency into three complementary aspects. Outcome consistency ($C_{\text{out}}$) measures whether the agent succeeds or fails consistently on repeated attempts at the same task. An insurance claims agent that approves a claim on one run but denies the identical claim on the next creates liability concerns and erodes user trust. Trajectory consistency captures whether the agent takes similar paths to its solutions, measured both distributionally ($C_{\text{traj}}^{d}$, comparing action type frequencies) and sequentially ($C_{\text{traj}}^{s}$, comparing action orderings). To illustrate, consider an order fulfillment agent: even if it successfully completes two identical orders, following different action sequences (e.g., sometimes charging the credit card before checking inventory, other times checking inventory first) creates different failure modes if the agent is interrupted mid-execution and complicates auditing for compliance. Finally, resource consistency ($C_{\text{res}}$) quantifies variability in computational and monetary costs. An agent whose latency, task completion duration, or API costs fluctuate by an order of magnitude across identical requests poses budgeting challenges for deployment.

#### Robustness (RRob\mathcal{R}_{\text{Rob}})

Real-world deployments expose agents to conditions that deviate from their training and evaluation environments/distributions. Robust agents should maintain comparable performance despite such perturbations. We identify the following three categories of perturbations that agents commonly encounter.

Fault robustness ($R_{\text{fault}}$) measures resilience to infrastructure failures: API timeouts, malformed responses, or temporary service unavailability. A robust agent should gracefully handle a web search tool returning an error rather than abandoning the task entirely or entering inconsistent states, for example by retrying or providing a fallback response. Environment robustness ($R_{\text{env}}$) captures sensitivity to changes in the agent’s operating environment that preserve semantic content—reordering JSON fields, changing date formats, renaming API parameters, or altering tool interfaces. More broadly, this dimension reflects the reality that deployed agents face environments that shift over time as APIs are updated, data schemas evolve, and tool interfaces change in production systems. Agents that fail when a database returns columns in a different order exhibit brittleness that limits their practical utility. Prompt robustness ($R_{\text{prompt}}$) measures invariance to semantically equivalent reformulations of instructions, whether rephrasings within a language or translations across languages. If a customer asking “I want to cancel my subscription” gets reliably helped but “please end my plan” causes the agent to fail, the system cannot be trusted to handle real user traffic where phrasing varies across users and contexts.

#### Predictability (RPred\mathcal{R}_{\text{Pred}})

Even agents that perform well on average provide limited value if users cannot anticipate when they will succeed or fail. In many deployment settings, users must decide whether to act on an output, seek verification, or defer to a human expert. Predictability captures whether an agent’s expressed confidence reliably indicates its actual performance and can therefore support such decisions.

Calibration ($P_{\text{cal}}$) measures whether stated confidence levels match empirical success rates: an agent claiming 80% confidence should succeed roughly 80% of the time. Poor calibration, such as consistent overconfidence, leads users to trust outputs they should instead verify, while under-confidence can result in unnecessary deferral. Discrimination ($P_{\text{AUROC}}$) assesses whether confidence scores successfully separate successes from failures. An agent that assigns 90% confidence to all outputs might be poorly calibrated, but if correct answers consistently receive higher scores than incorrect ones, the agent still discriminates well. Good discrimination enables users to set a confidence threshold above which outputs are accepted and below which they are deferred. The Brier score ($P_{\text{brier}}$) provides a proper scoring rule22A proper scoring rule incentivizes reporting true beliefs; deviation from the true probability worsens the expected score. that jointly measures calibration and discrimination, offering a holistic view of predictive quality.

#### Safety (RSaf\mathcal{R}_{\text{Saf}})

Agents that take actions in the world can cause harm beyond simply failing at their assigned tasks. Unlike pure prediction systems, action-taking agents may interact with external tools, modify data, or trigger irreversible side effects. Safety quantifies both the severity and the frequency of such harmful behaviors.

Compliance ($S_{\text{comp}}$) tracks adherence to predefined constraints—avoiding exposure of personally identifiable information, refraining from unauthorized actions, or staying within designated system boundaries. Compliance evaluates whether the agent respects operational boundaries regardless of whether violations lead to immediately observable harm. On the other hand, harm severity ($S_{\text{harm}}$) measures, among tasks that do violate constraints, how severe the consequences are. Consider a database management agent: returning query results in the wrong sort order is benign, but executing an unintended DELETE statement represents severe harm. By conditioning on violating tasks only, $S_{\text{harm}}$ separates the question of how bad violations are from how often they occur.

#### Aggregation

To enable upstream comparisons across agents, we aggregate reliability metrics within each dimension and compute an overall reliability score as follows:

The following aggregation choices merit explanation:

###### Disentangling Reliability & Capability

A fundamental principle guides all of our metric definitions: reliability should be disentangled from capability.
Raw task accuracy measures whether an agent succeeds; reliability measures how it succeeds and fails, i.e., the stability, predictability, robustness, and safety of its behavior.

Our metrics captures these distinctions through:

Normalization: For example, outcome consistency normalizes variance by $p(1-p)$, the maximum possible variance for a given success rate, isolating consistency from capability.

Ratio-based comparisons: Robustness metrics compute accuracy ratios between perturbed and nominal conditions, measuring relative degradation rather than absolute performance.

##### Disentangling Reliability & Capability

A fundamental principle guides all of our metric definitions: reliability should be disentangled from capability.
Raw task accuracy measures whether an agent succeeds; reliability measures how it succeeds and fails, i.e., the stability, predictability, robustness, and safety of its behavior.

Our metrics captures these distinctions through:

Normalization: For example, outcome consistency normalizes variance by $p(1-p)$, the maximum possible variance for a given success rate, isolating consistency from capability.

Ratio-based comparisons: Robustness metrics compute accuracy ratios between perturbed and nominal conditions, measuring relative degradation rather than absolute performance.

### 4 Experiments

We evaluate reliability on two established benchmarks that pose complementary challenges. Our goal is to understand the current state of agent reliability, both in aggregate and across individual sub-metrics, and how it has evolved over recent model generations.

#### Setup

#### Main Results

#### Connection to Real-World Failures

We further revisit the real-world failures from Section 1 (Replit agent, OpenAI Operator, NYC chatbot) to examine whether our metrics would have provided early warning signals. Our analysis in Table 3 concludes that each of the vulnerabilities could have been identified prior to deployment through systematic evaluation using our reliability metrics.

### 5 Recommendations

We have argued that agent reliability is a multi-dimensional property that cannot be inferred from mean task success alone. Treating reliability as an independent axis of progress has implications for how agents are evaluated, designed, and governed.

Our results suggest that benchmark design must fundamentally evolve. Current agent benchmarks typically report a single accuracy number from a single run in a fixed environment—such as a static database schema, a frozen set of API endpoints, or a fixed file system layout. This static, single-shot approach provides a misleadingly narrow view of capability. It reveals nothing about whether an agent would succeed on the same task tomorrow, how it handles a slightly rephrased instruction, or how it adapts when its underlying infrastructure shifts. Deployed agents operate in a fundamentally different reality: databases are migrated, API response formats change, tool libraries are updated, and the documents an agent must reason over are continuously revised. Measuring true reliability therefore requires a multifaceted approach. First, we need multi-run protocols that re-execute identical tasks to assess variance, alongside multi-condition protocols that systematically perturb user inputs. Second, benchmarks must become generative and parameterized rather than relying on fixed test sets. This allows experimenters to systematically alter the environment: renaming fields, reordering response structures, introducing new API versions, or injecting specific fault probabilities to mirror real-world distribution shifts. Generative test sets could also mitigate the risk of agents taking shortcuts such as looking up answers online rather than solving tasks genuinely [31]. Finally, temporal re-evaluation is critical. Re-running agents on these evolving benchmarks at regular intervals is essential to reveal whether reliability is robustly maintained or if it silently degrades as the world drifts away from the conditions under which the agent was originally tested.

Agent design should be explicitly guided by our reliability dimensions. Our empirical results reveal that reliability dimensions do not improve uniformly across model generations. Calibration and safety have improved noticeably in recent models, suggesting intentional optimization during training; though the proprietary nature of frontier pipelines prevents us from confirming this directly. By contrast, consistency and discrimination have improved little, suggesting that these dimensions are either harder to optimize or not yet the focus of current training pipelines. Systematic reliability evaluation makes this uneven progress visible: it identifies which dimensions are already on a positive trajectory and, more importantly, which are not. Where reliability gains are already occurring, our metrics help quantify and track them; where they are absent, they provide targets for future optimization. Whether or not current training pipelines already target our reliability dimensions, making these dimensions explicit and measurable enables more systematic progress than capability-oriented evaluation alone would.

Reliability metrics and incident analyses should feed into deployment decisions, change management, and regulatory compliance. For example, an organization could require minimum consistency and safety thresholds before promoting an agent from a sandboxed pilot to production, much as aviation systems must meet certification requirements before entering service. Analogous to safety-critical industries, a culture of incident reporting, post-mortem analysis, and continuous improvement will likely be crucial for agentic AI. Treating reliability as multi-dimensional also opens space for diverse research contributions: metric design, benchmark development, algorithmic methods, interface design, and governance mechanisms can all be evaluated through the lens of specific reliability dimensions rather than overall accuracy.

Beyond which reliability dimensions matter, a key determinant of how much reliability matters is whether an agent operates autonomously or augments a human collaborator. In augmentation settings (coding assistants, search copilots, brainstorming tools) a human reviews, edits, and approves the agent’s output before it takes effect. The human serves as a reliability backstop: an inconsistent suggestion is merely annoying, not dangerous, because it must pass through a human judgment filter. This has enabled AI coding assistants to reach widespread adoption despite imperfect reliability. Conversely, in automation settings (customer service chatbots, autonomous database management, unattended workflow execution) the agent’s output is the final action with no human buffer. Here, unreliability translates directly into real-world failures. This distinction suggests that the urgency of reliability improvements is not uniform across applications. For augmentation tools, moderate reliability may suffice because human oversight compensates for agent shortcomings. For automation, reliability is a hard prerequisite for deployment: an agent that succeeds on 90% of tasks but fails unpredictably on the remaining 10% may be a useful assistant yet an unacceptable autonomous system. As the field pushes toward greater agent autonomy, the reliability bar rises accordingly, making our reliability metrics increasingly essential.

### 6 Limitations

We acknowledge the following limitations of our work:

Benchmark coverage. Our empirical analysis covers two benchmarks ($\tau$-bench and GAIA), which, while complementary in structure and scope, represent a narrow slice of the diverse tasks agents will face in real-world practice.

Scaffold diversity. We evaluate each benchmark using a single scaffold that performs well on the respective benchmark; other scaffolds could yield qualitatively different reliability profiles. We plan to extend our evaluation to state-of-the-art agentic scaffolds such as Claude Code and OpenAI Codex as part of future work.

Safety judging. Our safety evaluation relies on LLM-based judging to achieve scalability, which introduces its own reliability concerns. Extending to judge-free and human-validated safety metrics is another important direction for future work.

Metric choices. The choice of specific metrics within each reliability dimension involves subjective decisions. Alternate decompositions are possible, and practitioners may reasonably disagree on which metrics best capture reliability for their specific application scenarios.

Safety aggregation. We report safety separately rather than incorporating it into the overall reliability score. This avoids masking tail risks through averaging but means the aggregate $\mathcal{R}$ does not capture the full reliability picture. We plan to explore principled approaches to integrating safety into the overall score in future work.

Capability disentanglement. Our approach to disentangling reliability from capability through normalization and conditioning is one of several possible strategies, and its adequacy may vary across deployment settings and task domains.

Choice of temperature. Where applicable, we set the temperature to zero in all our experiments. This limits one major source of stochasticity in model outputs. When attempting to maximize the accuracy of an agent, a nonzero temperature might be required, and our experiments might overestimate the reliability that is achievable in such circumstances.

We view our framework as a starting point and encourage the community to build on it by proposing alternative metrics and decompositions suited to different deployment contexts.
We also stress that reliability evaluation should complement, not replace, careful deployment practices including human oversight, sandboxed testing, monitoring, and ongoing performance assessment.

### 7 Conclusion

We introduced a decomposition of agent reliability grounded in safety-critical engineering and evaluated 14 models across two complementary benchmarks. Our results show that 18 months of rapid capability gains have produced only small improvements in reliability: models that are substantially more accurate remain inconsistent across runs, brittle to prompt rephrasings, and often fail to understand when they are likely to succeed.
As agents are deployed in high-stakes settings, treating reliability as a key evaluation concern becomes essential.
We have proposed one way to do so: a four-dimensional decomposition with 14 distinct sub-metrics grounded in safety-critical engineering. While our specific decomposition is one of many possible framings, the core shift in perspective matters most: from asking “How often does the agent succeed?” to asking “How predictably, consistently, robustly, and safely does it behave?”.
