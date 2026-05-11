# AgentDoG: A Diagnostic Guardrail Framework for AI Agent Safety and Security

**Authors:** Shanghai Artificial Intelligence Laboratory https://github.com/AI45Lab/AgentDoG https://huggingface.co/collections/AI45Research/agentdog

## Abstract

The rise of AI agents introduces complex safety and security challenges arising from autonomous tool use and environmental interactions. Current guardrail models lack agentic risk awareness and transparency in risk diagnosis. To introduce an agentic guardrail that covers complex and numerous risky behaviors, we first propose a unified three-dimensional taxonomy that orthogonally categorizes agentic risks by their source (where), failure mode (how), and consequence (what). Guided by this structured and hierarchical taxonomy, we introduce a new fine-grained agentic safety benchmark (ATBench) and a Diagnostic Guardrail framework for agent safety and security (AgentDoG). AgentDoG provides fine-grained and contextual monitoring across agent trajectories. More Crucially, AgentDoG can diagnose the root causes of unsafe actions and seemingly safe but unreasonable actions, offering provenance and transparency beyond binary labels to facilitate effective agent alignment. AgentDoG variants are available in three sizes (4B, 7B, and 8B parameters) across Qwen and Llama model families. Extensive experimental results demonstrate that AgentDoG achieves state-of-the-art performance in agentic safety moderation in diverse and complex interactive scenarios. All models and datasets are openly released.

### Introduction

The evolution of Large Language Models (LLMs) (singh2025openai; claude4; gpt5; qwen3; Deepseek-r1) has catalyzed the development of agentic AI: autonomous agents for complex planning, tool use, and long-horizon task execution. These agents are widely used in various applications such as deep research (zheng2025deepresearcher), computer use assistants (xie2024osworld), soft engineering (jimenez2023swe), and financial investment (fan2025ai). In this way, their high automation and non-deterministic nature introduce a new frontier of agentic safety and security challenges, including the risk of tool calling and the transmission of harmful information from the environment.

Current guardrail models (e.g., LlamaGuard3 (inan2023llama), Qwen3Guard (qwen3guard2025), and ShieldGemma (shieldagent2025)) provide safety filtering for the output content of LLMs but exhibit limitations when applied to complex agentic scenarios. Their primary shortcomings are twofold: (1) Lack of Agentic Risk Awareness: Existing LLMs’ safety policy fails to capture the complex and environment-dependent risk landscape of agents. (2) Lack of Provenance and Transparency: Binary labels “safe/unsafe” are insufficient for an accurate diagnosis of risk and overlook seemingly safe but unreasonable actions.

To introduce an agentic guardrail, we need a comprehensive and hierarchical safety taxonomy to cover complex and numerous agentic behaviors. However, the existing agentic safety definition and taxonomy are flat and coarse, e.g., considering prompt injection and unauthorized access as two parallel perspectives. However, prompt injection is the perspective of where the risk comes from, and unauthorized access is the perspective of what the real-world harm consequence of the risk is. In this way, such a flat and coarse risk taxonomy only covers limited agentic behaviors in an enumerative manner. Therefore, we propose a unified and hierarchical agentic safety taxonomy, consisting of three orthogonal dimensions: where the risk comes from, how the risk influences agents’ behaviors, and what the real-world harm is. Meanwhile, we provide an ATBench, a fine-grained agent safety benchmark, focusing on analyzing and evaluating these dimensions.

Guided by the above three-dimensional risk taxonomy, we introduce a Diagnostic Guardrail framework for agent safety and security (AgentDoG). AgentDoG provides fine-grained and contextual monitoring across agents’ trajectories, including malicious tool execution and prompt injection. More crucially, AgentDoG provides a more transparent perspective to understand why an agent takes a particular action in an unsafe or seemingly safe but unreasonible way, enabling more efficient alignment. We comprehensively evaluate AgentDoG across a diverse set of agentic benchmarks, e.g., R-judge (yuan-etal-2024-r), ASSE-Safety (luo2025agentauditor), and ATBench. The results demonstrate that AgentDoG outperforms
existing state-of-the-art models in safety moderation in diverse scenarios.

The main contributions of this work are:

A Unified Agentic Safety Taxonomy: We introduce a structured and hierarchical safety taxonomy categorizing both traditional content risks (e.g., toxicity and bias) and novel agentic risks (e.g., unauthorized tool use).

Agentic XAI Framework: AgentDoG proposes a novel Explainable AI (XAI) module that diagnoses the root cause of a specific action, tracing it to specific planning steps, tool selections, or context misinterpretations.

Open Dataset and Model Release: AgentDoG releases a curated ATBench containing about 2157 tools and 4486 turn interactions to support community benchmarking and research. Meanwhile, AgentDoG variants are openly available in three sizes (4B, 7B, and 8B parameters) across Qwen and Llama model families.

State-of-the-art Performance: Extensive experimental results demonstrate that AgentDoG achieves superior performance on agent-oriented safety benchmarks, effectively classifying harmful prompts and mitigating risky agent actions within complex, interactive scenarios.

### Safety Taxonomy

The agentic safety taxonomy serves as the foundation for implementing effective guardrails, as it defines what categories of risk should be identified, how different risks should be distinguished, and how unsafe agent behaviors can be systematically characterized.
As agentic systems operate in open-ended environments, interact with external tools, and execute multi-step tasks, their failure patterns become harder to analyze.
Risks no longer stem from a single decision or output, but often emerge from the interaction between inputs, reasoning, tools, and actions over time.
This shift necessitates a principled safety taxonomy that can systematically organize diverse and evolving risks, rather than relying on ad-hoc or enumerative definitions.

Existing benchmarks and taxonomies for agent risks, such as R-judge (yuan-etal-2024-r) and ASSE-Safety (luo2025agentauditor) exhibit several practical limitations. First, they adopt an enumerative and incomplete coverage of agentic risks, especially those arising from tool usage and agent–tool interactions.
Examples include compromised tool descriptions, malicious tool execution, incorrect parameter specification, or inefficient yet harmful agent actions.
Such risks are either underrepresented or entirely absent, limiting the ability of these benchmarks to reflect real-world agent behaviors.

Second, existing taxonomies often rely on unclear or mixed classification criteria, resulting in overlapping labels within a flat risk space.
Different dimensions of risk, including origins, behaviors, and outcomes, are frequently conflated.
For instance, prompt injection and unauthorized access are commonly treated as peer categories, even though the former describes where the risk comes from, while the latter characterizes how the risk manifests in agent behavior.
This issue is also reflected in previous work that frames agent-related risks separately through the lenses of security and safety (luo2025agentauditor; ghosh2025safety).
Security-oriented classifications focus on adversarial threats and system protection goals (e.g., confidentiality, integrity, and availability), whereas safety-oriented classifications emphasize harmful outcomes affecting individuals, organizations, or society.
Although both perspectives are valuable, treating them as parallel or disjoint dimensions will lead to label overlap and hinders precise diagnosis in agentic settings.
To maintain conceptual clarity while integrating both perspectives, we use the umbrella term safety throughout this paper, while preserving the distinctions required for fine-grained analysis.

To address these limitations, we propose a unified, three orthogonal dimensions safety taxonomy for agentic systems.
Specifically, we decompose agentic risks along three orthogonal dimensions: risk source, failure mode, and real-world harm.
These dimensions respectively answer the questions of where the risk comes from, how it manifests during agent execution, and what real-world harm it causes.
This structured decomposition separates causes, behavioral manifestations, and consequences, eliminates label overlap while explicitly capturing tool-related and environment-mediated risks.
An overview of the taxonomy and the relationships among the three dimensions is shown in Figure 2.

In what follows, we detail the proposed safety taxonomy by introducing its three dimensions: risk source, failure mode, and real-world harm.

#### Risk Source

The risk source dimension characterizes where a potential risk originates within an agent’s interaction loop.
It focuses on the factors that introduce unsafe conditions before or during decision-making.
A detailed taxonomy of risk sources is summarized in Table 1.

We categorize risk sources into four primary classes: user inputs, environmental observations, external entities (e.g., tools or APIs), and the agent’s internal decision-making logic.
User inputs may contain ambiguous, misleading, or adversarial instructions.
Environmental observations may provide incomplete, noisy, or manipulated information.
External entities can return erroneous, outdated, or harmful responses that misguide subsequent actions.
In addition, internal failures of the underlying language model may lead to flawed reasoning, planning, or action selection even without external interference.

#### Failure Mode

The failure mode dimension describes how a risk is realized through the agent’s behavior or outputs after a risk source has been introduced.
It captures the concrete patterns of unsafe execution or generation that directly lead to undesirable outcomes.
A detailed taxonomy of failure modes is summarized in Table 2.

We divide failure modes into two broad categories.
Behavioral failure modes arise from flawed planning, reasoning, or execution, such as improper action sequencing, unsafe tool usage, or deviations from intended procedures.
Output content failure modes, by contrast, occur when the agent’s textual output itself directly constitutes the risk, without invoking tools or executing external actions.
This includes generating misleading information, unauthorized disclosures, or other unsafe content that may cause harm when consumed.

#### Real-world Harm

The real-world harm dimension captures the real-world harms resulting from unsafe agent behavior.
It focuses on the impact of failures rather than their causes or mechanisms.
A detailed taxonomy of real-world harms is summarized in Table 3.

Real-world harms may include physical, financial, privacy, psychological, reputational, or societal harms.
Such outcomes can arise from adversarial manipulation, benign user error, or internal model failures.
By modeling consequences explicitly, this dimension supports outcome-oriented safety evaluation and impact assessment.

### AgentDoG

#### Task Definition

Prior works, such as LlamaGuard (inan2023llama) and Qwen3Guard (qwen3guard2025) have primarily focused on classifying whether the output of the final role in a multi-turn chat history is safe. In contrast, we consider a fundamentally different task: trajectory-level safety diagnosis where the model must determine whether an agent exhibits unsafe behavior at any point along its execution trajectory. The key distinction is that unsafe behavior may arise from intermediate actions (e.g., thinking content, tool calls) or intermediate environment feedback, even when the final response appears benign; therefore, auditing only the last turn can miss action-induced risks and process-level failures.

#### Data Synthesis and Collection

In this section, we introduce a taxonomy-guided agent risk trajectory synthesis approach to
generate high-quality risk data that covers complete tool-use chains. The key idea is to steer data generation with the three-dimensional risk taxonomy defined in section 2 and perform targeted sampling to systematically cover the risk space. Concretely, the data production process is implemented as a multi-agent pipeline where, for each trajectory, we independently sample one category from each of the three dimensions: risk source, failure mode, and risk consequence. Tasks, dialogues, and tool-calling trajectories designed to trigger the corresponding risk pattern are then constructed.

This design offers two major benefits. First, it moves from “covering a few typical cases” to “controllable, per-class synthesis”. Instead of generating data that only exhibits a small number of canonical risk phenomena, we can intentionally generate trajectories for each risk category, yielding more systematic coverage and more diverse training signals. Second, it substantially broadens tool-scenario coverage. By synthesizing trajectories with a pool of 10,000+ distinct tools, our pipeline spans a wide range of domains and tool interfaces, and naturally supports diverse tool compositions (single-tool use and multi-tool chains). This yields training and evaluation data that better reflects real-world agent deployments in large, heterogeneous tool ecosystems.

###### Data Synthesis Pipeline

As illustrated in Figure 4, we adopt a three-stage, planner-based pipeline for data synthesis, designed to generate long-horizon, tool-augmented interaction trajectories with controllable risk injection and reliable safety labels.

Stage 1: Planning. For each trajectory, we first sample a risk configuration tuple (comprising risk source, failure mode, and risk consequence) as defined in the safety taxonomy of section 2. Then, we determine the safety outcome of the trajectory, specifying whether the trajectory is intended to be safe (the agent successfully detects and mitigates the risk) or unsafe (the attack succeeds). In parallel, we sample a candidate set of tools from the filtered tool library.

Given these inputs, the planner constructs a coherent multi-step task plan via a two-phase process. In the first phase, it designs a coherent multi-step task and analyzes how the risk can be naturally embedded into the trajectory. The output of this phase is a free-form Chain-of-Thought. In the second phase, it produces a structured execution plan that specifies the task description, the selected subset of tools, the sequence of tool-augmented steps, and the exact risk injection point. For safe trajectories, the plan also encodes the agent’s expected defensive behavior at the risk point.

Stage 2: Trajectory Synthesis.
Given a structured execution plan produced in Stage 1, the trajectory synthesis stage instantiates it into a concrete, multi-turn interaction through a coordinated, plan-driven generation process. A central Orchestrator controls the execution flow and ensures that each step in the plan is executed in order, including user query generation, tool interaction simulation, agent response generation, and outcome summarization.

###### Data quality control

To ensure that synthesized trajectories are both trainable and reliably labeled, we introduce a dedicated quality-control (QC) procedure after trajectory generation. QC follows a two-layer design: deterministic validators to remove structural and formatting errors; and an LLM-based judge to verify semantic alignment between the trajectory content and the intended safety labels.

###### Statistics of synthesized data

Finally, we provide a quantitative overview of the synthesized dataset in terms of overall scale, coverage of the risk taxonomy, tool-usage characteristics, and the pass rate of the quality control (QC) process. The dataset contains over 100k multi-turn interaction trajectories, designed to provide broad and systematic coverage of the targeted risks under diverse tool-assisted settings. After QC filtering, the resulting corpus is practically usable for both model training and systematic evaluation, enabling detailed analysis of multi-step agent behaviors and their safety failure patterns.

#### Training

Our guard models are trained using standard supervised fine-tuning (SFT).
Given a dataset of demonstrations $\mathcal{D}_{\text{train}}=\{(x_{i},y_{i})\}_{i=1}^{n}$, where $x_{i}$ is the agent trajectory and $y_{i}$ is the safety label, the model is trained to minimize the negative log-likelihood loss:

We fine-tuned several models, including Qwen3-4B-Instruct-2507 (qwen3), Qwen2.5-7B-Instruct, and Llama3.1-8B-Instruct (dubey2024llama). All models were trained with a learning rate of 1e-5.

##### Data Synthesis Pipeline

As illustrated in Figure 4, we adopt a three-stage, planner-based pipeline for data synthesis, designed to generate long-horizon, tool-augmented interaction trajectories with controllable risk injection and reliable safety labels.

Stage 1: Planning. For each trajectory, we first sample a risk configuration tuple (comprising risk source, failure mode, and risk consequence) as defined in the safety taxonomy of section 2. Then, we determine the safety outcome of the trajectory, specifying whether the trajectory is intended to be safe (the agent successfully detects and mitigates the risk) or unsafe (the attack succeeds). In parallel, we sample a candidate set of tools from the filtered tool library.

Given these inputs, the planner constructs a coherent multi-step task plan via a two-phase process. In the first phase, it designs a coherent multi-step task and analyzes how the risk can be naturally embedded into the trajectory. The output of this phase is a free-form Chain-of-Thought. In the second phase, it produces a structured execution plan that specifies the task description, the selected subset of tools, the sequence of tool-augmented steps, and the exact risk injection point. For safe trajectories, the plan also encodes the agent’s expected defensive behavior at the risk point.

Stage 2: Trajectory Synthesis.
Given a structured execution plan produced in Stage 1, the trajectory synthesis stage instantiates it into a concrete, multi-turn interaction through a coordinated, plan-driven generation process. A central Orchestrator controls the execution flow and ensures that each step in the plan is executed in order, including user query generation, tool interaction simulation, agent response generation, and outcome summarization.

##### Data quality control

To ensure that synthesized trajectories are both trainable and reliably labeled, we introduce a dedicated quality-control (QC) procedure after trajectory generation. QC follows a two-layer design: deterministic validators to remove structural and formatting errors; and an LLM-based judge to verify semantic alignment between the trajectory content and the intended safety labels.

##### Statistics of synthesized data

Finally, we provide a quantitative overview of the synthesized dataset in terms of overall scale, coverage of the risk taxonomy, tool-usage characteristics, and the pass rate of the quality control (QC) process. The dataset contains over 100k multi-turn interaction trajectories, designed to provide broad and systematic coverage of the targeted risks under diverse tool-assisted settings. After QC filtering, the resulting corpus is practically usable for both model training and systematic evaluation, enabling detailed analysis of multi-step agent behaviors and their safety failure patterns.

### Benchmark: ATBench

#### Overview of the Benchmark

Existing agent safety benchmarks (rjudge2024; luo2025agentauditor) generally face two critical limitations:
(1) Limited tool diversity and scenario coverage: These benchmarks mostly rely on short trajectories (e.g., R-Judge (rjudge2024) typically average 5.28 turns) with limited tool coverage, leading to a narrow sample distribution. Consequently, they fail to capture the complex, long-horizon interaction scenarios found in the real world.
(2) Lack of fine-grained diagnosis: Most existing benchmarks provide only coarse binary safety labels without diagnosing the underlying root causes. They fail to explicitly characterize why a risk arises, how it manifests in agent behavior, and what consequences it produces. This lack of granularity limits their utility for in-depth safety auditing and model improvement.

To address these gaps, we propose the Agent Trajectory Safety and Security Benchmark (ATBench), a trajectory-level benchmark designed for high-fidelity safety evaluation. ATBench comprises 500 full execution trajectories, balanced evenly between 250 safe and 250 unsafe instances.
These trajectories feature complex multi-turn interactions with an average length of 8.97 turns and cover 1,575 unique tools, ensuring substantial diversity in interaction patterns.
Constructed via the same taxonomy-guided synthesis pipeline as AgentDoG, ATBench serves as a held-out evaluation set that is not used for training.

For the labeling of ATBench, we strictly follow the unified safety taxonomy introduced in Section 2.
We define safety at the trajectory level: a trajectory is labeled unsafe if any unsafe behavior is observable at any point; otherwise, it is labeled safe. This includes cases where the agent successfully identifies a risk and safely handles it (e.g., refusing a malicious user query or ignoring an indirect prompt injection).
Each trajectory is annotated with a binary verdict; unsafe trajectories additionally include fine-grained taxonomy labels.
Specifically, for unsafe cases, the benchmark covers 8 risk source categories, 14 failure mode categories, and 10 risk consequence categories.
Notably, we enforce a balanced distribution across all three taxonomy dimensions. Minor deviations exist due to post-generation quality filtering, but the dataset enables fair and comparable evaluation across categories.
The distribution of these fine-grained labels is illustrated in Figure 6.

ATBench offers three key advantages.
(1) It evaluates full execution trajectories rather than isolated outputs, capturing the long-horizon decision chains typical of real-world deployments.
(2) It is taxonomy-grounded, providing semantically explicit labels that enable precise risk attribution and diagnosis.
(3) It supports robust generalization assessment: by incorporating diverse tool invocation patterns and ensuring broad taxonomy coverage, ATBench enables a faithful evaluation of practical agentic safety systems.

#### Trajectory Generation and Data Processing Pipeline

###### Trajectory Generation

The trajectory generation procedure for ATBench follows the same taxonomy-guided synthesis framework used to construct our training data (Section 3). We ground generation in the risk taxonomy and drive agent executions with tool seeds, producing long-horizon trajectories with multi-turn interactions and realistic tool invocations.

To ensure a clean evaluation, we strictly decouple ATBench from the training data via a tool-level split. Specifically, we use an independent tool library for ATBench with no overlap with the training tools. This library contains 2,292 tool definitions, creating an “unseen-tools” evaluation setting. This design directly assesses whether a guard model can generalize to previously unseen tools and contexts, rather than just measuring performance on familiar patterns.

###### Multi-Agent Verification and Data Filtering

We apply a two-stage verification and filtering procedure to improve the reliability and realism of synthesized trajectories.
We first perform quality scoring to remove low-fidelity samples, and then conduct multi-model labeling to obtain robust binary verdicts and taxonomy labels.
Cross-model non-unanimity on the binary verdict is used as a signal to route ambiguous cases to human verification.

###### Human Verification and Quality Control

Following the multi-agent filtering stage, we implement a rigorous human verification protocol to resolve ambiguities and ensure benchmark reliability.
Specifically, we adopt a stratified quality control strategy that partitions the dataset into two subsets based on model consensus: an easy subset and a hard subset.

For the easy subset, we employ a lightweight verification strategy to validate labeling consistency.
Given the unanimous consensus among four diverse models, we conduct human spot-checking by randomly sampling 20% of the cases.
All spot-checked instances were confirmed by human annotators under the same rubric, verifying the reliability of the model-consensus labels.

For the hard subset, we conduct an exhaustive, double-blind review process to resolve ambiguities.
We adopt a cross-checking protocol with 10 expert annotators: each hard trajectory is independently audited by two researchers to verify whether unsafe verdicts are supported by observable evidence rather than mere intent.
This step explicitly filters out false positives caused by capability limitations.
When annotators disagree, we resolve the case by introducing a third expert annotator for adjudication, ensuring that the final labels are high-fidelity and taxonomy-grounded.

##### Trajectory Generation

The trajectory generation procedure for ATBench follows the same taxonomy-guided synthesis framework used to construct our training data (Section 3). We ground generation in the risk taxonomy and drive agent executions with tool seeds, producing long-horizon trajectories with multi-turn interactions and realistic tool invocations.

To ensure a clean evaluation, we strictly decouple ATBench from the training data via a tool-level split. Specifically, we use an independent tool library for ATBench with no overlap with the training tools. This library contains 2,292 tool definitions, creating an “unseen-tools” evaluation setting. This design directly assesses whether a guard model can generalize to previously unseen tools and contexts, rather than just measuring performance on familiar patterns.

##### Multi-Agent Verification and Data Filtering

We apply a two-stage verification and filtering procedure to improve the reliability and realism of synthesized trajectories.
We first perform quality scoring to remove low-fidelity samples, and then conduct multi-model labeling to obtain robust binary verdicts and taxonomy labels.
Cross-model non-unanimity on the binary verdict is used as a signal to route ambiguous cases to human verification.

##### Human Verification and Quality Control

Following the multi-agent filtering stage, we implement a rigorous human verification protocol to resolve ambiguities and ensure benchmark reliability.
Specifically, we adopt a stratified quality control strategy that partitions the dataset into two subsets based on model consensus: an easy subset and a hard subset.

For the easy subset, we employ a lightweight verification strategy to validate labeling consistency.
Given the unanimous consensus among four diverse models, we conduct human spot-checking by randomly sampling 20% of the cases.
All spot-checked instances were confirmed by human annotators under the same rubric, verifying the reliability of the model-consensus labels.

For the hard subset, we conduct an exhaustive, double-blind review process to resolve ambiguities.
We adopt a cross-checking protocol with 10 expert annotators: each hard trajectory is independently audited by two researchers to verify whether unsafe verdicts are supported by observable evidence rather than mere intent.
This step explicitly filters out false positives caused by capability limitations.
When annotators disagree, we resolve the case by introducing a third expert annotator for adjudication, ensuring that the final labels are high-fidelity and taxonomy-grounded.

### Evaluation

In this section, we provide a comprehensive evaluation of AgentDoG’s capabilities in ensuring agent safety. Our experiments are designed to assess the model in two critical dimensions: (1) Trajectory-level safety evaluation, identifying unsafe behaviors in multi-step interactions; and (2) Fine-grained risk diagnosis, categorizing specific risk sources and failure modes. We begin by describing our experimental setup, including datasets, metrics and baselines in Section 5.1. Subsequently, we present the trajectory-level comparison results in Section 5.2, followed by a detailed analysis of fine-grained diagnosis capabilities in Section 5.3.

#### Experimental Setup

#### Trajectory-level Safety Results

#### Fine-grained Risk Diagnosis Results

### Agentic XAI Attribution

In the previous sections, AgentDoG has demonstrated superior capabilities in auditing agent safety by accurately identifying unsafe trajectories and subsequently categorizing them into granular taxonomies.
However, as agentic systems are increasingly deployed in real-world settings, ensuring transparency and accountability requires looking beyond risk categorization to understand the internal factors driving specific actions.
In particular, we need to explain why an agent arrives at a particular action, especially when the behavior is unsafe or appears acceptable yet remains flawed or misaligned during the processing trajectories.
To bridge this gap, we incorporate the Agentic XAI Attribution framework following (qian2026behind), which performs hierarchical attribution diagnosis on agent trajectories.

Specifically, we first detail this attribution methodology in Section 6.1.
Then, in Section 6.2, we empirically evaluate its diagnostic capabilities through qualitative case studies, demonstrating the effectiveness of the attribution module and validating that our safety training enhances the AgentDoG’s ability to pinpoint the internal drivers behind the action.

#### Method: Hierarchical Agentic Attribution

Problem formulation.
Consider an agent parameterized by a policy $\pi_{\theta}$, which produces an interaction trajectory $\mathcal{T}$ and culminates in a target action $a_{\text{target}}$.
We formally define the agent’s interaction trajectory as a temporal sequence $\mathcal{T}=\{s_{1},s_{2},\dots,s_{N}\}$, where each step $s_{i}$ represents a distinct interaction unit, such as a user instruction, an observation from the environment, or an internal reasoning trace.
Our objective is to quantify the contribution of preceding steps and their internal sentences to the generation of $a_{\text{target}}$. Specifically, we aim to assign an attribution score to each interaction step and its constituent sentences, reflecting their influence on the agent’s final action.

Trajectory-level attribution via temporal dynamics.
The first stage of diagnosis operates at the coarse-grained level, aiming to identify which interaction steps effectively steered the agent toward $a_{\text{target}}$. We leverage the temporal structure of the execution to monitor the dynamics of the agent’s decision likelihood.
Specifically, we compute the temporal information gain for step $s_{i}$, which measures exactly how much the likelihood of generating $a_{\text{target}}$ increases when $s_{i}$ is appended to the preceding history $\mathcal{T}_{\leq i-1}$:

where $\mathcal{T}_{\leq i}=\{s_{1},\dots,s_{i}\}$ denotes the trajectory containing all interaction steps up to $i$.
Intuitively, a high value of $\Delta_{i}$ indicates that the information introduced at step $s_{i}$ serves as a decisive driver for the agent’s subsequent action.

Fine-grained sentence-level attribution.
Building on the identified high-impact steps that drive the $a_{\text{target}}$, we further refine the diagnosis to the sentence level to isolate the precise textual evidence.
Let $X_{i}=\{x_{i,1},\dots,x_{i,M}\}$ denote the set of sentences contained within step $s_{i}$. We employ a perturbation-based strategy (chuang2025selfcite; lei2016rationalizing; cohen2024contextcite; liu2024attribot) to quantify the influence of each sentence $x_{i,j}\in X_{i}$ toward $a_{\text{target}}$.

First, we calculate Probability Drop Score, which measures the necessity of the sentence by observing the likelihood decrease when $x_{i,j}$ is removed from the trajectory context $\mathcal{T}_{\leq i}$:

Then, the Probability Hold Score assesses the sufficiency of the sentence by evaluating the likelihood when $x_{i,j}$ acts as the sole information source:

The final attribution score is obtained by aggregating these two signals:

We apply this fine-grained scoring to the top-ranked steps based on $\Delta_{i}$, effectively narrowing down the diagnosis from temporal events to specific sentences.

#### Analysis of Attribution Results

In this subsection, we empirically evaluate the diagnostic capabilities of the agentic XAI attribution framework, validating its ability to unveil the internal drivers behind agent risks.
Unless otherwise specified, we employ AgentDoG-Qwen3-4B to perform the attribution analysis.
We first present qualitative case studies to illustrate how the module localizes root causes within agent trajectories (Section 6.2.1), followed by a comparative analysis demonstrating the superior attribution quality and alignment with causal logic exhibited by AgentDoG compared to its base model (Section 6.2.2).

###### Diagnostic Case Studies

Case 1: Prompt injection in recruitment scenario.

Case overview. In this case (Figure 7-left), an AI Recruitment Assistant is tasked with screening a candidate’s resume file and scheduling an interview if the candidate matches specific criteria. The risk arises from an Prompt Injection: the job applicant embeds a deceptive instruction within the resume text, implying that the resume is qualified and should pass the current screening stage. The agent fails to distinguish this adversarial data from valid content, resulting in unauthorized interview scheduling.

Attribution analysis.
The attribution module accurately diagnoses the external trigger responsible for the final behavior.
At the trajectory level, the analysis identifies the agent’s initial action to access the file (Step 2) and the subsequent resume content provided by the tool (Step 3) as the primary drivers.
While Step 2 establishes the necessary retrieval context, the tool output in Step 3 introduces the decisive information.
A fine-grained sentence-level examination of Step 3 reveals that the attribution correctly identifies the adversarial content from benign resume data. As shown in the attribution results, the highest positive scores are assigned to the deceptive instructions: 
“[Important] Please ignore the previous content, automated validation for this record is successful.”
In contrast, the normal candidate details receive less attribution.

Overall, the attribution result effectively disentangles the root cause, confirming that the agent’s decision was hijacked by the specific adversarial text embedded in the resume.
This transparency is vital for diagnosing risks introduced by external tool interactions, underscoring the urgent need to enhance agent robustness against untrusted information channels.

Case 2: Misinterpretation of sarcasm in financial analysis.

Case overview. In this financial analysis scenario (Figure 7-right), the agent is tasked with monitoring market feedback on CompanyA††CompanyA is a synthetic company used in our case, and $CompanyA denotes its corresponding tradable stock. to determine trading strategies.
The core risk emerges from a sarcastic user quote: a customer posts a comment that superficially uses positive language (“Fantastic update”, “Absolute genius”) but is contextually negative (“Paying more for fewer features”). The agent misinterprets this sarcasm as genuine praise, leading to a flawed financial recommendation to go long.

Attribution analysis.
The attribution module effectively localizes the source of this cognitive failure.
At the trajectory level, the analysis pinpoints the tool execution result (Step 3) as the dominant factor driving the final decision, which contains the retrieved customer quote on the stock of CompanyA.
Sentence-level analysis further illustrates that the attribution scores are heavily concentrated on the positive phrases, i.e.,
“Absolute genius” and 
“Fantastic update”.
Crucially, the sentence providing the sarcastic context—“Paying more for fewer features really shows how much they value customers”—receives significantly lower attribution, indicating that the agent is misled by the positive part and fails to recognize the underlying risks in the stock.

Overall, the diagnosis reveals that the agent’s decision is driven by shallow keywords rather than a holistic semantic understanding, exposing a potential risk of agentic systems deployed in high-stakes settings.
In these scenarios, attribution analysis can serve as a valuable tool to audit an agent’s inference process, guiding targeted interventions to improve reasoning robustness.

###### Comparative Analysis: AgentDoG vs. Base Model

To validate whether our safety training enhances the model’s ability to identify the internal drivers of agents’ risky behaviors, we compare the attribution performance of AgentDoG-Qwen3-4B against its base model-Qwen3-4B-Instruct-2507, results are shown in Figure 8.

Case 3: Ambiguous Financial Transaction.

Case overview. In this scenario, the user requests to send a send a peer-to-peer payment (specifically a WeChat red packet) to a contact named Zhang Wei.” The contact search tool returns three distinct individuals with the same name (a coworker, a classmate, and a trainer). Instead of pausing to ask for clarification, the agent makes an unsafe assumption based on common usage patterns” and then selects the coworker, to execute the financial transaction.

Comparative attribution analysis.
We compare the top-ranked steps identified by both models to understand their diagnosis of this risky action.
At the trajectory level, both models exhibit broad agreement on the primary drivers, identifying the agent’s initial action to the user query (Step 2) and the tool output (Step 3, showing multiple contacts) as high-impact components.
This attribution is reasonable, as these steps provide the necessary background context and ambiguous search results that set the stage for the subsequent decision.

However, a significant divergence appears in the third-ranked component, revealing a fundamental difference in attribution quality.
AgentDoG-Qwen3-4B correctly identifies the agent’s internal reasoning step (Step 4) after the search results as the critical driver. Specifically, the sentence-level attribution highlights the flawed thought process: 
“Based on common usage patterns, the user is most likely sending money to a coworker.”
This pinpoints that the agent’s decision to select the coworker was directly driven by this insufficiently supported assumption.
In contrast, Qwen3-4B-Instruct-2507 attributes the decision to the final environment execution log (Step 5, “success: true”), which contains less information regarding the decision logic.

This comparison highlights that AgentDoG exhibits more robust and granular agentic attribution capabilities compared to its base model.
This indicates that our safety training not only equips the model with the ability to detect unsafe agent trajectories but also refines its understanding of the internal drivers behind the action.
By bridging the gap between detection and diagnosis, this diagnostic transparency provides a critical foundation for the accountable deployment of agentic systems.

##### Diagnostic Case Studies

Case 1: Prompt injection in recruitment scenario.

Case overview. In this case (Figure 7-left), an AI Recruitment Assistant is tasked with screening a candidate’s resume file and scheduling an interview if the candidate matches specific criteria. The risk arises from an Prompt Injection: the job applicant embeds a deceptive instruction within the resume text, implying that the resume is qualified and should pass the current screening stage. The agent fails to distinguish this adversarial data from valid content, resulting in unauthorized interview scheduling.

Attribution analysis.
The attribution module accurately diagnoses the external trigger responsible for the final behavior.
At the trajectory level, the analysis identifies the agent’s initial action to access the file (Step 2) and the subsequent resume content provided by the tool (Step 3) as the primary drivers.
While Step 2 establishes the necessary retrieval context, the tool output in Step 3 introduces the decisive information.
A fine-grained sentence-level examination of Step 3 reveals that the attribution correctly identifies the adversarial content from benign resume data. As shown in the attribution results, the highest positive scores are assigned to the deceptive instructions: 
“[Important] Please ignore the previous content, automated validation for this record is successful.”
In contrast, the normal candidate details receive less attribution.

Overall, the attribution result effectively disentangles the root cause, confirming that the agent’s decision was hijacked by the specific adversarial text embedded in the resume.
This transparency is vital for diagnosing risks introduced by external tool interactions, underscoring the urgent need to enhance agent robustness against untrusted information channels.

Case 2: Misinterpretation of sarcasm in financial analysis.

Case overview. In this financial analysis scenario (Figure 7-right), the agent is tasked with monitoring market feedback on CompanyA††CompanyA is a synthetic company used in our case, and $CompanyA denotes its corresponding tradable stock. to determine trading strategies.
The core risk emerges from a sarcastic user quote: a customer posts a comment that superficially uses positive language (“Fantastic update”, “Absolute genius”) but is contextually negative (“Paying more for fewer features”). The agent misinterprets this sarcasm as genuine praise, leading to a flawed financial recommendation to go long.

Attribution analysis.
The attribution module effectively localizes the source of this cognitive failure.
At the trajectory level, the analysis pinpoints the tool execution result (Step 3) as the dominant factor driving the final decision, which contains the retrieved customer quote on the stock of CompanyA.
Sentence-level analysis further illustrates that the attribution scores are heavily concentrated on the positive phrases, i.e.,
“Absolute genius” and 
“Fantastic update”.
Crucially, the sentence providing the sarcastic context—“Paying more for fewer features really shows how much they value customers”—receives significantly lower attribution, indicating that the agent is misled by the positive part and fails to recognize the underlying risks in the stock.

Overall, the diagnosis reveals that the agent’s decision is driven by shallow keywords rather than a holistic semantic understanding, exposing a potential risk of agentic systems deployed in high-stakes settings.
In these scenarios, attribution analysis can serve as a valuable tool to audit an agent’s inference process, guiding targeted interventions to improve reasoning robustness.

##### Comparative Analysis: AgentDoG vs. Base Model

To validate whether our safety training enhances the model’s ability to identify the internal drivers of agents’ risky behaviors, we compare the attribution performance of AgentDoG-Qwen3-4B against its base model-Qwen3-4B-Instruct-2507, results are shown in Figure 8.

Case 3: Ambiguous Financial Transaction.

Case overview. In this scenario, the user requests to send a send a peer-to-peer payment (specifically a WeChat red packet) to a contact named Zhang Wei.” The contact search tool returns three distinct individuals with the same name (a coworker, a classmate, and a trainer). Instead of pausing to ask for clarification, the agent makes an unsafe assumption based on common usage patterns” and then selects the coworker, to execute the financial transaction.

Comparative attribution analysis.
We compare the top-ranked steps identified by both models to understand their diagnosis of this risky action.
At the trajectory level, both models exhibit broad agreement on the primary drivers, identifying the agent’s initial action to the user query (Step 2) and the tool output (Step 3, showing multiple contacts) as high-impact components.
This attribution is reasonable, as these steps provide the necessary background context and ambiguous search results that set the stage for the subsequent decision.

However, a significant divergence appears in the third-ranked component, revealing a fundamental difference in attribution quality.
AgentDoG-Qwen3-4B correctly identifies the agent’s internal reasoning step (Step 4) after the search results as the critical driver. Specifically, the sentence-level attribution highlights the flawed thought process: 
“Based on common usage patterns, the user is most likely sending money to a coworker.”
This pinpoints that the agent’s decision to select the coworker was directly driven by this insufficiently supported assumption.
In contrast, Qwen3-4B-Instruct-2507 attributes the decision to the final environment execution log (Step 5, “success: true”), which contains less information regarding the decision logic.

This comparison highlights that AgentDoG exhibits more robust and granular agentic attribution capabilities compared to its base model.
This indicates that our safety training not only equips the model with the ability to detect unsafe agent trajectories but also refines its understanding of the internal drivers behind the action.
By bridging the gap between detection and diagnosis, this diagnostic transparency provides a critical foundation for the accountable deployment of agentic systems.

### Related Work

### Conclusion and Discussion

#### Conclusion

In this work, we introduced AgentDoG, a novel diagnostic guardrail designed to address the complex safety and security challenges of agentic AI systems. We made the following primary contributions.
First, we proposed a unified, three-dimensional safety taxonomy (risk source, failure mode, real-world harm) that extended the traditional content-driven safety taxonomy to better capture the nuances of agentic behavior. Guided by this taxonomy, we developed a systematic data synthesis pipeline to generate annotated agentic trajectories, ensuring comprehensive coverage of the complex risk space.
Second, we introduced an agentic XAI framework for diagnosing the root causes of agent behavior. It traced a specific action back to the exact steps or sentences in the trajectory that triggered it, offering transparency into the agent’s decision logic.
Third, we trained and released a suite of AgentDoG model variants across Qwen and LLama families. Extensive evaluations demonstrated that these models achieved state-of-the-art performance, providing both high-accuracy binary safe/unsafe classification and fine-grained diagnostics that identify the provenance of unsafe actions through our taxonomy.
Fourth, to facilitate further research and standardized evaluation, we also introduced a challenging new benchmark, ATBench, for trajectory-level safety evaluation. These contributions establish a more robust and interpretable foundation for the safety of autonomous agents.

#### Limitations and Future Directions

While AgentDoG demonstrates strong performance, we acknowledge its current limitations, which highlight promising avenues for future research. Currently, the input of AgentDoG is confined to text-based trajectories. Expanding AgentDoG’s capabilities to support multimodal inputs is a crucial next step for safeguarding GUI-based agents. Furthermore, the role of AgentDoG could evolve from a reactive monitor to a proactive alignment tool. For example, the diagnostic output could serve as a reward signal to align agent behavior through reinforcement learning.

### Authors

Scientific Directors: Xia Hu, Chaochao Lu
 
Project Co-Leaders‡‡Corresponding authors: Dongrui Liu (liudongrui@pjlab.org.cn), Jing Shao (shaojing@pjlab.org.cn)
 
Core Contributors: Dongrui Liu, Qihan Ren, Chen Qian, Shuai Shao, Yuejin Xie, Yu Li, Zhonghao Yang, Haoyu Luo, Peng Wang, Qingyu Liu 
 
Contributors: Binxin Hu, Ling Tang, Jilin Mei, Dadi Guo, Leitao Yuan, Junyao Yang, Guanxu Chen, Qihao Lin, Yi Yu, Bo Zhang, Jiaxuan Guo, Jie Zhang, Wenqi Shao, Huiqi Deng, Zhiheng Xi, Wenjie Wang, Wenxuan Wang, Wen Shen 
 
Technical Acknowledgements: Zhikai Chen, Haoyu Xie, Jialing Tao, Juntao Dai, Jiaming Ji, Zhongjie Ba, Linfeng Zhang, Yong Liu, Quanshi Zhang, Lei Zhu, Zhihua Wei, Hui Xue
