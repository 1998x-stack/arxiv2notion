# \model: Synergizing Reasoning and Acting in Language Models

**Authors:** Shunyu Yao, Jeffrey Zhao, Dian Yu, Nan Du, Izhak Shafran, Karthik Narasimhan, Yuan Cao

## Abstract

While large language models (LLMs) have demonstrated impressive performance across tasks in language understanding and interactive decision making, their abilities for reasoning (e.g. chain-of-thought prompting) and acting (e.g. action plan generation) have primarily been studied as separate topics. In this paper, we explore the use of LLMs to generate both reasoning traces and task-specific actions in an interleaved manner, allowing for greater synergy between the two: reasoning traces help the model induce, track, and update action plans as well as handle exceptions, while actions allow it to interface with and gather additional information from external sources such as knowledge bases or environments. We apply our approach, named \model, to a diverse set of language and decision making tasks and demonstrate its effectiveness over state-of-the-art baselines in addition to improved human interpretability and trustworthiness. Concretely, on question answering (HotpotQA) and fact verification (Fever), \model overcomes prevalent issues of hallucination and error propagation in chain-of-thought reasoning by interacting with a simple Wikipedia API, and generating human-like task-solving trajectories that are more interpretable than baselines without reasoning traces. Furthermore, on two interactive decision making benchmarks (ALFWorld and WebShop), \model outperforms imitation and reinforcement learning methods by an absolute success rate of 34% and 10% respectively, while being prompted with only one or two in-context examples.

### Introduction

A unique feature of human intelligence is the ability to seamlessly combine task-oriented actions with verbal reasoning (or inner speech,  Alderson-Day & Fernyhough, 2015), which has been theorized to play an important role in human cognition for enabling self-regulation or strategization (Vygotsky, 1987; Luria, 1965; Fernyhough, 2010) and maintaining a working memory (Baddeley, 1992).
Consider the example of cooking up a dish in the kitchen. Between any two specific actions, we may reason in language in order to track progress (“now that everything is cut, I should heat up the pot of water”), to handle exceptions or adjust the plan according to the situation (“I don’t have salt, so let me use soy sauce and pepper instead”), and to realize when external information is needed (“how do I prepare dough? Let me search on the Internet”).
We may also act (open a cookbook to read the recipe, open the fridge, check ingredients) to support the reasoning and to answer questions (“What dish can I make right now?”).
This tight synergy between “acting” and “reasoning” allows humans to learn new tasks quickly and perform robust decision making or reasoning, even under previously unseen circumstances or facing information uncertainties.

Recent results have hinted at the possibility of combining verbal reasoning with interactive decision making in autonomous systems.
On one hand, properly prompted large language models (LLMs) have demonstrated emergent capabilities to carry out several steps of reasoning traces to derive answers from questions in arithmetic, commonsense, and symbolic reasoning tasks (Wei et al., 2022). However, this “chain-of-thought” reasoning is a static black box, in that the model uses its own internal representations to generate thoughts and is not grounded in the external world,
which limits its ability to reason reactively or update its knowledge. This can lead to issues like fact hallucination and error propagation over the reasoning process (Figure 1 (1b)).
On the other hand, recent work has explored the use of pre-trained language models for planning and acting in interactive environments (Ahn et al., 2022; Nakano et al., 2021; Yao et al., 2020; Huang et al., 2022a), with a focus on predicting actions via language priors. These approaches usually convert multi-modal observations into text, use a language model to generate domain-specific actions or plans, and then use a controller to choose or execute them.
However, they do not employ language models to reason abstractly about high-level goals or maintain a working memory to support acting, barring Huang et al. (2022b) who perform a limited form of verbal reasoning to reiterate spatial facts about the current state.
Beyond such simple embodied tasks to interact with a few blocks, there have not been studies on how reasoning and acting can be combined in a synergistic manner for general task solving, and if such a combination can bring systematic benefits compared to reasoning or acting alone.

In this work, we present \model, a general paradigm to combine reasoning and acting with language models for solving diverse language reasoning and decision making tasks (Figure 1).
\model prompts LLMs to generate both verbal reasoning traces and actions pertaining to a task in an interleaved manner, which allows the model to perform dynamic reasoning to create, maintain, and adjust high-level plans for acting (reason to act), while also interact with the external environments (e.g. Wikipedia) to incorporate additional information into reasoning (act to reason).

We conduct empirical evaluations of \model and state-of-the-art baselines on four diverse benchmarks: question answering (HotPotQA, Yang et al., 2018), fact verification (Fever, Thorne et al., 2018), text-based game (ALFWorld, Shridhar et al., 2020b), and webpage navigation (WebShop, Yao et al., 2022).
For HotPotQA and Fever, with access to a Wikipedia API that the model can interact with, \model outperforms vanilla action generation models while being competitive with chain-of-thought reasoning (CoT) (Wei et al., 2022). The best approach overall is a combination of \model and CoT that allows for the use of both internal knowledge and externally obtained information during reasoning.
On ALFWorld and WebShop, two or even one-shot \model prompting is able to outperform imitation or reinforcement learning methods trained with $10^{3}\sim 10^{5}$ task instances, with an absolute improvement of 34% and 10% in success rates respectively. We also demonstrate the importance of sparse, versatile reasoning in decision making by showing consistent advantages over controlled baselines with actions only.
Besides general applicability and performance boost, the combination of reasoning and acting also contributes to model interpretability, trustworthiness, and diagnosability across all domains, as humans can readily distinguish information from model’s internal knowledge versus external environments, as well as inspect reasoning traces to understand the decision basis of model actions.

To summarize, our key contributions are the following:
(1) we introduce \model, a novel prompt-based paradigm to synergize reasoning and acting in language models for general task solving;
(2) we perform extensive experiments across diverse benchmarks to showcase the advantage of \model in a few-shot learning setup over prior approaches that perform either reasoning or action generation in isolation;
(3) we present systematic ablations and analysis to understand the importance of acting in reasoning tasks, and reasoning in interactive tasks;
(4) we analyze the limitations of \model under the prompting setup (i.e. limited support of reasoning and acting behaviors), and perform initial finetuning experiments showing the potential of \model to improve with additional training data.
Scaling up \model to train and operate on more tasks and combining it with complementary paradigms like reinforcement learning could further unlock the potential of large language models.

### \model: Synergizing Reasoning + Acting

Consider a general setup of an agent interacting with an environment for task solving. At time step $t$, an agent receives an observation $o_{t}\in\mathcal{O}$ from the environment and takes an action $a_{t}\in\mathcal{A}$ following some policy $\pi(a_{t}|c_{t})$, where $c_{t}=(o_{1},a_{1},\cdots,o_{t-1},a_{t-1},o_{t})$ is the context to the agent. Learning a policy is challenging when the mapping $c_{t}\mapsto a_{t}$ is highly implicit and requires extensive computation.
For example, the agent shown in Figure 1(1c) is unable to generate the correct final action (Act 4) to finish the QA task as it requires complex reasoning over the trajectory context (Question, Act 1-3, Obs 1-3).
Similarly, the agent shown in Figure 1(2a) fails to comprehend from the context that sinkbasin 1 does not contain peppershaker 1, thus keep producing hallucinating actions.

The idea of \model is simple: we augment the agent’s action space to $\mathcal{\hat{A}}=\mathcal{A}\cup\mathcal{L}$, where $\mathcal{L}$ is the space of language. An action $\hat{a}_{t}\in\mathcal{L}$ in the language space, which we will refer to as a thought or a reasoning trace, does not affect the external environment, thus leading to no observation feedback. Instead, a thought $\hat{a}_{t}$ aims to compose useful information by reasoning over the current context $c_{t}$, and update the context $c_{t+1}=(c_{t},\hat{a}_{t})$ to support future reasoning or acting.
As shown in Figure 1, there could be various types of useful thoughts, e.g. decomposing task goals and create action plans (2b, Act 1; 1d, Thought 1), injecting commonsense knowledge relevant to task solving (2b, Act 1), extracting important parts from observations (1d, Thought2, 4), track progress and transit action plans (2b, Act 8), handle exceptions and adjust action plans (1d, Thought 3), and so on.

However, as the language space $\mathcal{L}$ is unlimited, learning in this augmented action space is difficult and requires strong language priors. In this paper, we mainly focus on
the setup where a frozen large language model, PaLM-540B (Chowdhery et al., 2022)11We show some GPT-3 (Brown et al., 2020) results in Appendix A.1, which outperforms PaLM-540B., is prompted with few-shot in-context examples to generate both domain-specific actions and free-form language thoughts for task solving (Figure 1 (1d), (2b)). Each in-context example is a human trajectory of actions, thoughts, and environment observations to solve a task instance (see Appendix C).
For the tasks where reasoning is of primary importance (Figure 1(1)), we alternate the generation of thoughts and actions so that the task-solving trajectory consists of multiple thought-action-observation steps.
In contrast, for decision making tasks that potentially involve a large number of actions (Figure 1(2)), thoughts only need to appear sparsely in the most relevant positions of a trajectory, so we let the language model decide the asynchronous occurrence of thoughts and actions for itself.

Since decision making and reasoning capabilities are integrated into a large language model, \model enjoys several unique features:
A) Intuitive and easy to design: Designing \model prompts is straightforward as human annotators just type down their thoughts in language on top of their actions taken. No ad-hoc format choice, thought design, or example selection is used in this paper. We detail prompt design for each task in Sections 3 and 4.
B) General and flexible: Due to the flexible thought space and thought-action occurrence format, \model works for diverse tasks with distinct action spaces and reasoning needs, including but not limited to QA, fact verification, text game, and web navigation.
C) Performant and robust: \model shows strong generalization to new task instances while learning solely from one to six in-context examples, consistently outperforming baselines with only reasoning or acting across different domains. We also show in Section 3 additional benefits when finetuning is enabled, and in Section 4 how \model performance is robust to prompt selections.
D) Human aligned and controllable: \model promises an interpretable sequential decision making and reasoning process where humans can easily inspect reasoning and factual correctness. Moreover, humans can also control or correct the agent behavior on the go by thought editing, as shown in Figure 5 in Section 4.

### Knowledge-Intensive Reasoning Tasks

We begin with knowledge-intensive reasoning tasks like multi-hop question answering and fact verification.
As shown in Figure 1(1d), by interacting with a Wikipedia API, \model is able to retrieve information to support reasoning, while also use reasoning to target what to retrieve next, demonstrating a synergy of reasoning and acting.

#### Setup

#### Methods

#### Results and Observations

### Decision Making Tasks

We also test \model on two language-based interactive decision-making tasks, ALFWorld and WebShop,
both of which feature complex environments that require agents to act over long horizons with sparse rewards, warranting the need for reasoning to act and explore effectively.

### Related Work

### Conclusion

We have proposed \model – a simple yet effective method for synergizing reasoning and acting in large language models. Through a diverse set of experiments on multi-hop question-answering, fact checking, and interactive decision-making tasks, we show that \model leads to superior performance with interpretable decision traces. Despite the simplicity of our method, complex tasks with large action spaces require more demonstrations to learn well, which unfortunately can easily go beyond the input length limit of in-context learning. We explore the fine-tuning approach on HotpotQA with initial promising results, but learning from more high-quality human annotations will be the desiderata to further improve the performance. Scaling up \model with multi-task training and combining it with complementary paradigms like reinforcement learning could result in stronger agents that further unlock the potential of LLMs for more applications.

##### Acknowledgments

We thank the support and feedback of many people from Google Brain team and Princeton NLP Group.
This work was supported in part by the National Science Foundation under Grant No. 2107048. Any opinions, findings, and conclusions or recommendations expressed in this material are those of the author(s) and do not necessarily reflect the views of the National Science Foundation.

##### Reproducibility Statement

Our main experiments are done on PaLM (Chowdhery et al., 2022), which is not an openly accessible model yet. To increase reproducibility, we have included all used prompts in Appendix C, additional experiments using GPT-3 (Brown et al., 2020) in Appendix A.1, and associated GPT-3 \model prompting code at https://anonymous.4open.science/r/ReAct-2268/.

##### Ethics Statement

prompts large language models to generate more human interpretable, diagnosable, and controllable task-solving trajectories than previous methods.
However, hooking up a large language model with an action space to interact with external environments (e.g. the web, physical environments) has potential dangers, e.g.  looking up inappropriate or private information, or taking harmful actions in an environment.
Our experiments minimize such risks by limiting the interactions to specific websites (Wikipedia or WebShop) that are free of private information, without any dangerous actions in the action space design
(i.e. models cannot really buy products on WebShop the research benchmark, or edit Wikipedia).
We believe researchers should be aware of such risks before designing more extensive experiments in the future.
