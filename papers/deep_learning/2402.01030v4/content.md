# Executable Code Actions Elicit Better LLM Agents

**Authors:** Xingyao Wang1, Yangyi Chen1, Lifan Yuan1, Yizhe Zhang2, Yunzhu Li1, Hao Peng1, Heng Ji1 1 University of Illinois Urbana-Champaign, 2 Apple 1{xingyao6,yangyic3,yunzhuli,haopeng,hengji}@illinois.edu 2yizhe_zhang@apple.com

## Abstract

Large Language Model (LLM) agents, capable of performing a broad range of actions, such as invoking tools and controlling robots, show great potential in tackling real-world challenges. LLM agents are typically prompted to produce actions by generating JSON or text in a pre-defined format, which is usually limited by constrained action space (e.g., the scope of pre-defined tools) and restricted flexibility (e.g., inability to compose multiple tools). This work proposes to use executable Python code to consolidate LLM agents’ actions into a unified action space (CodeAct). Integrated with a Python interpreter, CodeAct can execute code actions and dynamically revise prior actions or emit new actions upon new observations through multi-turn interactions. Our extensive analysis of 17 LLMs on API-Bank and a newly curated benchmark shows that CodeAct outperforms widely used alternatives (up to 20% higher success rate). The encouraging performance of CodeAct motivates us to build an open-source LLM agent that interacts with environments by executing interpretable code and collaborates with users using natural language. To this end, we collect an instruction-tuning dataset CodeActInstruct that consists of 7k multi-turn interactions using CodeAct. We show that it can be used with existing data to improve models in agent-oriented tasks without compromising their general capability. CodeActAgent, finetuned from Llama2 and Mistral, is integrated with Python interpreter and uniquely tailored to perform sophisticated tasks (e.g., model training) using existing libraries and autonomously self-debug.111The code, data, model, and an online demo for practitioners to try out are available at https://github.com/xingyaoww/code-act.

### Introduction

Large Language Models (LLMs) have emerged as a pivotal breakthrough in natural language processing (NLP).
When augmented with action modules that allow access to APIs, their action space expands beyond conventional text processing, allowing LLMs to acquire capabilities such as tool invocation and memory management [30, 41] and venture into real-world tasks such as controlling robots [1, 19, 29] and performing scientific experiments [3].

We inquire: how to effectively expand LLM agents’ action space for solving complex real-world problems?
Much existing research has examined using text [62, 34, inter alia] or JSON [40, 5, inter alia] to produce actions (e.g., tool uses in Fig. 1 top left).
However, both methods typically suffer from constrained scope of action spaces (actions are usually tailored for specific tasks) and restricted flexibility (e.g., inability to compose multiple tools in a single action).
As an alternative approach, several work [26, 44, 48] demonstrate the potential of using LLMs to generate code to control robots or game characters.
However, they typically rely on pre-specified control primitives and hand-engineered prompts and, more importantly, struggle to dynamically adjust or emit actions based on new environmental observation and feedback.

This work proposes CodeAct, a general-purpose framework that allows LLMs to generate executable Python code as actions (Fig. 1 top right).
CodeAct is designed to handle a variety of applications and comes with unique advantages:

Integrated with a Python interpreter, CodeAct can execute code actions and dynamically adjust prior actions or emit new action based on observations it receives through multiple turns of interactions (code execution).

Code actions allow LLM to leverage existing software packages. CodeAct can use readily available Python packages for an expanded action space instead of hand-crafted task-specific tools [64, 42]. It also allows LLM to use automated feedback (e.g., error messages) implemented in most software to improve task-solving by self-debugging its generated code [8, 52].

Code data is widely used in pre-training today’s LLMs [58].
These models are already familiar with structured programming languages, allowing cost-effective adoption of CodeAct.

Compared to JSON and text with a pre-defined format, code inherently supports control and data flow, allowing for the storage of intermediate results as variables for reuse and the composition of multiple tools to perform complex logical operations (e.g., if-statements, for-loops) with one piece of code, thereby unlocking LLMs’ potential to tackle complex tasks by leveraging its pre-trained knowledge of programming.
In Fig. 1, an LLM using with CodeAct (top right) can apply the same sequence of tools (e.g., passing one tool’s output as input to another tool using the data flow feature) to all inputs through for-loops (i.e., control flow feature) with one action; while text or JSON have to take action for every input (top left).

Our extensive experiments with 17 LLMs (including both open-source and proprietary ones) confirm the above benefits (3
& 4) of CodeAct.
To demonstrate benefit (3), our first experiment (§2.2) compares CodeAct to baselines on basic tasks involving atomic tool use (i.e., only one tool is used per action), ablating the control and data flow advantage offered by CodeAct.
The results show that, for most LLMs, CodeAct achieves comparable or better performance than the baselines.
CodeAct’s performance gains are more prominent on complex tasks, as demonstrated in our second experiment (benefit 4).
We curate a new benchmark consisting of 82 human-curated tasks that typically require multiple calls to multiple tools in multi-turn interactions (M3ToolEval; §2.3).
Problems in this benchmark often require intricate coordination and composition of multiple tools.
With its strengths in control and data flow, CodeAct achieves up to a 20% absolute improvement over baselines on the success rate of solving the problems while requiring up to 30% fewer actions.
These performance gains widen as the capabilities of the LLMs increase (Fig. 1 bottom).

The promising performance of CodeAct motivates an open-source LLM agent that can effectively act through CodeAct, and collaborate with humans through natural language.
To this end, we collect an instruction-tuning dataset CodeActInstruct consisting of 7k high-quality multi-turn interaction trajectories with CodeAct (§3.1).
CodeActInstruct is motivated by a general agent framework consisting of agent, user, and environments (Fig. 2) and focuses on agent-environment interactions with the computer (information seeking, software package use, external memory) and the physical world (robot planning).
On CodeActInstruct, we perform careful data selection to promote the capability of improving from multi-turn interaction (e.g., self-debug).
We show that CodeActInstruct can be used with commonly used instruction tuning data to improve the models’ performance in agent tasks without compromising their general capabilities (e.g., knowledge-based QA, coding, instruction following, §3.2).
Our model, dubbed CodeActAgent, is finetuned from LLaMA-2 [47] and Mistral-7B [20] and improves on out-of-domain agent tasks with not only CodeAct, but also text action in a pre-defined format (§3.2).

CodeAct can further benefit from multi-turn interactions and existing software (benefit 1 & 2, §2.4).
As shown in Fig. 3, CodeActAgent, designed for seamless integration with Python, can carry out sophisticated tasks (e.g., model training, data visualization) using existing Python packages. Error messages from the environment further enable it to rectify errors autonomously through self-debugging in multi-turn interaction.
Thanks to LLM’s extensive programming knowledge acquired during pre-training, these are achieved without needing in-context demonstrations, reducing the human efforts for adapting CodeActAgent to different tasks.

### CodeAct Makes LLMs Better Agents

In this section, we first describe CodeAct framework (§2.1) and provide empirical evidence that supports the choice of CodeAct.
We focus on Python as the programming language for CodeAct due to its popularity (ranked top-1 at TIOBE index [46]) and numerous open-source packages.
We aim to answer several research questions (RQs) using 17 off-the-shelf LLMs. In §2.2, we examine RQ1: Does LLMs’ familiarity with code due to a large amount of code pre-training data bring CodeAct advantages over text and JSON?
We discuss RQ2 in §2.3: Does CodeAct benefit from Python’s innate control and data flow feature in complex problems?
Finally, as an additional benefit, we discuss how using CodeAct further enhances LLM agents by enabling multi-turn interactions and allowing them to access existing software in §2.4 and Fig. 3.

#### What is CodeAct?

In Fig. 2, we first introduce a general multi-turn interaction framework for LLM agents’ real-world usage that considers three roles: agent, user, and environment.
We define interaction as the information exchange between the agent and an external entity (user or environment).
For each turn of interaction, the agent receives an observation (input) either from the user (e.g., natural language instruction) or the environment (e.g., code execution result), optionally planning for its action through chain-of-thought [56], and emits an action (output) to either user in natural language or the environment.
CodeAct employs Python code to consolidate all actions for agent-environment interaction. In CodeAct, each emitted action to the environment is a piece of Python code, and the agent will receive outputs of code execution (e.g., results, errors) as observation.
We include an example prompt of CodeAct in §E.

#### CodeAct Shows the Promise as a Strong Tool Use Framework

In this section, we perform a controlled experiment to understand which format (text, JSON, CodeAct) is more likely to lead an LLM to generate correct atomic tool calls.
The performance in this experiment reflects LLM’s familiarity with the corresponding format.
We hypothesize that using CodeAct to call tools is a more natural way to use tools for the models, which typically have extensive exposure to code data during their training.

Setup.
We re-purpose API-Bank [24] and test LLMs’ API-calling performance, comparing CodeAct, JSON, and text actions.
For each evaluation instance, we instruct LLM to generate one atomic tool call in the format of a Python function call, JSON object, or text expression in a pre-defined format. A concrete example is shown in Tab. A.6.
We use API-Bank’s level-1 instructions and the provided toolset. To evaluate API-calling, we follow their correctness metric, matching the ground-truth API outputs with the actual model-generated API’s execution outputs.

Results.
We present results in Tab. 3.
For most LLMs, CodeAct achieves comparable or better performance even in atomic actions (the simplistic tool use scenario) where its control and data flow strengths are ablated.
Compared to closed-source LLMs, CodeAct’s improvements are more prominent in open-source models. Furthermore, code data is usually more accessible for fine-tuning open-source LLMs than the specialized JSON or text tool-calling format.
Although JSON is consistently weaker than other approaches for open-source models, it achieves decent performance with closed-source LLMs, indicating that these closed-source models may have gone through targeted fine-tuning toward their JSON capabilities.
These results suggest optimizing for CodeAct is a better route for open-source LLMs than alternatives to improve their tool-use capabilities, as they already show good initial CodeAct capability due to extensive exposure to code data during pre-training.

#### CodeAct Gets More Done with Fewer Interactions

In this section, we investigate whether LLM agents can benefit from the control and data flow of code on problems that require complex patterns of tool use.

M3ToolEval.
As shown in Tab. A.7, to the best of our knowledge, no existing tool-use benchmarks contain complex tasks requiring the composition of multiple tools while supporting evaluating different action formats. Hence, we curate a benchmark M3ToolEval to fill this gap, which evaluates LLMs’ capabilities in solving complex tasks that typically require multiple calls to multiple tools in multi-turn interactions.
It contains 82 human-curated instances, spanning tasks including web browsing, finance, travel itinerary planning, science, and information processing.
Each domain is accompanied by a unique set of manually crafted tools.
We intentionally keep the prompt simple and avoid providing any task demonstration to test the LLM’s zero-shot ability to use tools, similar to how a novice user without domain knowledge of few-shot prompting would use the model.
Please refer to §F for prompt examples.

Setup.
We allow the model to generate fully functional Python code that enables control and data flow (e.g., if-statement, for-loop). We follow the action format for JSON and text described in Tab. A.6.
Within each turn, the model can either emit an action or propose an answer to be verified by an exact match with the ground-truth solution.
The interaction will terminate when a maximum of 10 interaction turns are reached or a correct solution has been submitted, similar to MINT [53].

Metric. We measure the success rate by calculating the percentage of the model proposed answers that match the ground-truth solutions. We also include the avg. turns metric: the average number of turns on all evaluated instances.

Quantitative Results on M3ToolEval.
We include full results in Tab. 3 and a subset of results for visualization in Fig. 1.
CodeAct generally has a higher task success rate (12 out of 17 evaluated LLMs), similar to the trend in §2.2. Moreover, using CodeAct requires a lower average number of turns (12 out of 17 evaluated LLMs).
For example, the best model gpt-4-1106-preview achieves a $20.7$% absolute improvement compared to the next best action format (text) while requiring $2.1$ fewer interaction turns on average.
However, there is still a significant gap in terms of absolute CodeAct performance between open- and closed-source LLMs as the best open-source model achieving 13.4% while the best closed-source model gpt-4-1106-preview 74.4%. This is potentially due to open-source models’ weak task-solving capability and inability to follow complex instructions without demonstration, suggesting an urgent need to improve open-source LLMs for practical, real-world tasks under the zero-shot setting.

#### CodeAct Benefits from Multi-turn Interactions and Existing Software Packages

In Fig. 3, we show how an LLM agent can integrate with Python (i.e., CodeActAgent we trained in §3.2) and use existing software to perform complex tasks in multi-turn interactions.
Thanks to its extensive knowledge of Python learned during pre-training, the LLM agent can automatically import the correct Python libraries to solve tasks without requiring user-provided tools or demonstrations.
As illustrated in Fig. 3, CodeActAgent can use Pandas to download and process tabular data, use Scikit-Learn for machine learning train-test data split and regression model training, and use Matplotlib for data visualization.
Furthermore, using the interactive Python interpreter for code execution allows automated error messages that help the LLM agent ‘self-debug’ their actions in a multi-turn interaction and eventually complete the human user’s request correctly.

### Empowering Open-source LLM Agent to be Better at CodeAct

The promising results achieved by CodeAct motivate us to build an open-source LLM agent that can both interact with environments through CodeAct and communicate with humans using language.
To improve open-source LLMs’ CodeAct capability, in §3.1, we introduce CodeActInstruct, an instruction finetuning dataset that contains agent-environment interaction trajectories.
We discuss data selection procedures in §3.1 to promote improvement from interaction behavior.
Additionally, we show that CodeAct can be used together with existing agent-user conversation data (§4) to balance the dialog capability of the resulting LLM.
Our model CodeActAgent, finetuned from LLaMA-2 [47] and Mistral-7B [20] on a mixture of CodeActInstruct and general conversations, improves CodeAct performances without hurting LLM’s general performance on a diverse suite of tasks (§3.2).

#### CodeActInstruct: Agent-Environment Interactions

We consider four main use cases in agent-environment interaction and repurpose five existing datasets across different domains to generate trajectories:

Information Seeking: We use a training subset of HotpotQA [59] to generate information-seeking trajectories, where LLMs use the wikipedia_search API (provided as a Python function) to search for information to answer questions.

Software Package (Tool) Usage: We use the training set of code generation problems in APPS [16] and math problems in MATH [18]. The code generation tasks already involve importing packages and/or creating new tools by defining a new Python function. For MATH, we provide an in-context demonstration of importing Python packages (e.g., sympy for symbolic math) for problem-solving.

External Memory: We repurpose the training subset of WikiTableQuestion [35] and tweak it into two variants of tabular reasoning tasks that require accessing external memory: (1) SQL-based, requiring the LLM to interact with an SQL database through sqlite3 package to answer the question via SQL execution; (2) Pandas-based, requiring the model to interact with pandas tables to perform data operations (e.g., select, filter). Examples of instructions can be found in §G.3.1.

Robot Planning: We use ALFWorld [43], a text-only embodied environment simulator, to generate trajectories that use robot-control APIs (repurposed as Python function) to complete household tasks. Following MINT [53], we provide an in-context demonstration to encourage the use of for-loop and if-statement code blocks to automate repetitive operations (e.g., searching for items by visiting different locations).

Data Down-sampling.
We down-sample each dataset by keeping only the most challenging instances, aiming to make trajectory generation more efficient and cost-effective. Furthermore, it also helps remove simple instances that existing LLMs can already solve.
The statistics of the filtered dataset can be found in Tab. A.9. Please refer to §G.1 for details about the down-sample process.

Repurpose Data for Multi-turn Interaction.
Some datasets (APPS, MATH, WikiTableQuestions) are initially single-turn problems that expect one solution per instruction, whereas, in a realistic agent use case, we often require multi-turn interaction to complete each task (Fig. 1 top).
Following MINT [53], we repurpose single-turn problems into multi-turn ones by allowing LLM to interact with the environment for multiple turns before it decides to submit one solution for evaluation.
Specifically for code generation problems, we provide an in-context example to guide LLMs to test their solution on provided test cases before they submit the solution.
Metrics from the original data will evaluate the submitted solution to determine its correctness. We include prompt examples in §G.3.

Trajectory Generation.
We use MINT’s evaluation framework [53] to generate interaction trajectories for the aforementioned datasets and determine the correctness of each trajectory.
We run gpt-3.5-turbo-0613 from OpenAI, claude-1-instant and claude-2 from Anthropic on down-sampled data, except code generation, which we use a longer-context version of GPT-3.5 (gpt-3.5-turbo-0613-16k) due to the long-context requirement of the self-debugging process.
On a subset of problems that none of these models can solve, we use gpt-4-0613 to generate trajectories.

Enhancing Agent’s Capabilities of Improving from Interaction.

We select a high-quality subset of all the generated trajectories from CodeActInstruct to promote the agent’s ability to improve the next action based on prior observations (e.g., self-debugging from code execution error message, a planning capability in Fig. 2).
To achieve this, we selectively preserve those trajectories wherein the model initially encounters errors but rectifies these inaccuracies in later interactions.
For these instances, the LLM typically engages in self-reflection following the initial error, thereby proactively enhancing its future actions.
Other filtering details are discussed in §G.2.
On all trajectories generated, we keep 411 trajectories from gpt-4-0613 and 6728 trajectories from gpt-3.5 and claude.
The statistics of the resulting dataset CodeActInstruct are shown in Tab. 4.

Comparing CodeActInstruct with Prior Work.
Compared with prior work AgentInstruct [65] and FireAct [6] that mainly focus using text as action, CodeActInstruct results in models that are more practical in real-world implementation, as such models using CodeAct can directly interact with Python interpreters and open-source toolkits (Fig. 3), reducing the development effort for action parsing and tool creations.
CodeActInstruct is systematically constructed following the general agent framework (Fig. 2).
It covers diverse domains (e.g., compared to FireAct that only considers QA-task and search API), contains quality data (e.g., promotes agent’s capability of self-debug) and of larger size (3.8x / 3.5x more data trajectories and 5x / 19x more tokens compared to AgentInstruct / FireAct respectively in Tab. 4).
As we empirically show in Tab. 5, the resulting model (same backbone) of CodeActInstruct achieves 24% and 119% relative improvement compared to AgentInstruct and FireAct.

CodeActInstruct Can Be Used With Existing Agent-User Conversation Data.

We use a sub-sampled set of OpenOrca [25] that focuses on single-turn chain-of-thought (CoT) reasoning, ShareGPT [2, 32] from two sources that contain multi-turn conversations between human and LLM, and CapyBara [22] that focuses on reasoning in multi-turn conversations.
Details of down-sampling can be found in §C.
Please refer to Tab. 4 for statistics of general conversations.

#### CodeActAgent

We fine-tune Llama-2 7B [47] and Mistral 7B [20] on a mixture of CodeActInstruct and general conversations (Tab. 4) to obtain CodeActAgent.

Training Setup. We perform full-parameter supervised fine-tuning with a sequence length of 4,096 tokens for Llama-2 and 16,384 for Mistral. Please refer to §D for more details.

Evaluation Setup.
We use MINT [53] to evaluate LLMs with CodeAct on a diverse range of agent tasks.
CodeActAgent has some training domains overlapping with MINT’s evaluation (i.e., MINT includes ALFWorld and MATH), hence we report separate numbers for MINT’s in- and out-of-domain performance.
Unless otherwise specified, we measure MINT tasks’ success rates with interaction turn $k=5$.
We also evaluate out-of-domain agent tasks using text actions from MiniWob++ (computer tasks, [21]) and ScienceWorld (text-based simulator for elementary science curriculum, [50]) to test whether CodeActAgent can generalize to different action formats.
Finally, we include a suite of general LLM evaluation tasks to assess general capability: MMLU [17] for knowledge-based QA, HumanEval [7] for single-turn code-generation, GSM8K [12] for single-turn tool-free math reasoning, and MTBench [67] for instruction-following.

CodeActAgent Excels in CodeAct Task.
As shown in Tab. 5, CodeActAgent (both variants) perform better than all evaluated open-source LLMs on both the in-domain and out-of-domain subsets of MINT.
On M3ToolEval, we find CodeActAgent (Mistral) outperforms open-source LLMs of similar size (7B and 13B) and even reaches similar performance to those 70B models (Tab. 3).
Surprisingly, no improvement is observed for the Llama-2 variant. We discuss the potential reasons in §H.

CodeActAgent Generalizes to Text Action.
When evaluated on out-of-domain text actions, CodeActAgent (LLaMA2, 7B), which has never been optimized for text action, achieves comparable performance to AgentLM-7B [65] which has explicit tuning for text actions.

CodeActAgent Maintains or Improves the Performance on General LLM Tasks.
In Tab. 5, we find that CodeActAgent (both variants) performs better on generic LLM tasks we tested, except for a slight degradation on MMLU for CodeActAgent (Mistral, 7B).

Ablation Study.
Tab. A.8 presents ablation experiments to determine the importance of CodeActInstruct and general conversations.
Both CodeActInstruct and general conversations contribute to agent tasks, while general conversations are essential to maintain performance on general tasks.

### Related Work

#### Action Module in LLM Agents

As detailed in [49], LLM-based autonomous agents are typically structured around four components: customized profiles [34, 37], long-term memory capabilities [68, 14], reasoning and planning algorithms [56, 10], and, most crucially, action modules.
The action modules are key to facilitating LLM agents to effectively interact with external entities, including humans [23] and tools [39] in the environment [53].
In this study, we address the critical problem of standardizing the action space for LLM agents.
We further discuss the difference between CodeAct and the line of work that uses code generation for problem-solving in §A.
We notice a concurrent study TaskWeaver [38] similarly endorses the use of code. We discuss the principal distinctions in §B.

#### Improving LLM Agents

Two primary methods for enhancing LLM agents are prompt engineering and instruction tuning, as surveyed by [49].
For prompt engineering [27], numerous strategies have been introduced to improve the chain-of-thought reasoning [56], including self-consistency-based reasoning [54, 10] and tree-based approaches [61].
Moreover, LLMs can be strategically prompted to reflect on previous plans [63, 55, 66], enabling them to refine initial actions through trial and error.
Contrast to prompt engineering, instruction tuning intrinsically enhances LLMs [11], particularly in their agent capabilities [65, 6].
For effective training, human annotators can curate expert demonstrations for specific agent tasks, such as web browsing [60, 31].
To minimize human annotation efforts, prior work creates synthetic datasets using stronger LLMs to distill agent capabilities into local models, focusing on tool usage [40], interaction [9], and social skills [28].
CodeActInstruct aligns with the latter approach and creates datasets using stronger LLMs due to limited resources for annotation.

### Conclusions

This work introduces CodeAct that employs executable Python code for the LLM agent’s action, which is advantageous over using text or JSON action, especially in complex scenarios.
We collect CodeAct-focused multi-turn interaction trajectories CodeActInstruct for instruction tuning, and train CodeActAgent that is specially designed for seamless integration with Python and can execute sophisticated tasks (e.g., model training) leveraging existing Python packages and autonomously rectifying errors through self-debugging.

### Broader Impacts, Limitations, and Future Work

This paper presents work whose goal is to advance LLM-based autonomous agents that can communicate with humans through natural language and assist human users by performing tasks in environments on behalf of humans.
In this section, we discuss potential societal consequences, limitations, and future work related to our work and its goal.

CodeActAgent is an initial prototype of an autonomous agent and still has several practical limitations. For example, it may suffer from hallucination commonly seen in LLMs (e.g., imagine the content of a variable without actually printing it out), suggesting the need for subsequent alignment [33] for further improvements.

Despite being a prototype, CodeActAgent has already demonstrated limited self-improving capability (e.g., self-debug error messages to improve its action) and the ability to interact with environments.
Future work may build upon CodeActAgent to develop better agents by having them perform extensive interactions within a given environment and iteratively bootstrap their self-improving capability to learn to improve from past mistakes.
More powerful agents, as results of such algorithms, are potentially beneficial for solving a wide range of real-world problems (e.g., theorem proving, drug discovery).
As extensively discussed in [13], a fully autonomous agent may transform the current landscape of the labor market and impact the jobs of existing workers.

Furthermore, since CodeAct directly grants access for the agent to freely execute code in a sandbox environment, in the worst scenario (e.g., in Sci-Fi movies), such an agent may potentially break free of the sandbox restriction and cause harm to the world through cyber-attack, highlighting the need for future work to design better safety mechanism to safeguard autonomous agents.
